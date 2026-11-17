"""
GRUPO EMPROS - Sistema profesional de Gestión de Inventarios
"""
import os
from datetime import datetime, timedelta, date
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_file, jsonify
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

from config import conectar_db
from services.stats_service import (
    obtener_resumen_periodo, productos_bajo_minimo,
    ultimos_movimientos, generar_snapshot_semanal, historial_semanas
)
from services.pdf_service import generar_reporte_inventario

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "15ea22a503dc52a4cd5dffa1acb6e5ec31270f8d511f2bb18c8fed3a5cada37f"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

csrf = CSRFProtect(app)


# ───────────────────────── Decoradores ─────────────────────────

def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def administrador_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        if session.get("rol") != "administrador":
            flash("Acceso denegado. Solo administradores.", "error")
            return redirect(url_for("inicio"))
        return f(*args, **kwargs)
    return decorated


def solo_lectura_empleado(f):
    """Permite a empleados ver, pero bloquea POST/PUT/DELETE."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        if session.get("rol") == "empleado" and request.method != "GET":
            flash("Los empleados solo tienen permiso de visualización.", "error")
            return redirect(request.referrer or url_for("inicio"))
        return f(*args, **kwargs)
    return decorated


# ───────────────────────── Auth ─────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")

        conexion = None
        cursor = None
        try:
            conexion = conectar_db()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, nombre, password_hash, rol, activo
                FROM usuarios
                WHERE usuario = %s
            """, (usuario,))
            user = cursor.fetchone()

            if user and user["activo"] and check_password_hash(user["password_hash"], password):
                session.clear()
                session["usuario_id"] = user["id"]
                session["nombre"] = user["nombre"]
                session["rol"] = user["rol"]
                session["usuario"] = usuario
                flash(f"Bienvenido, {user['nombre']}", "success")
                return redirect(url_for("inicio"))

            flash("Usuario o contraseña incorrectos.", "error")
        except Exception as e:
            app.logger.exception("Error en login")
            flash("Error de conexión. Intenta de nuevo.", "error")
        finally:
            if cursor:
                cursor.close()
            if conexion and conexion.is_connected():
                conexion.close()

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_requerido
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("login"))


# ───────────────────────── Dashboard ─────────────────────────

@app.route("/")
@login_requerido
def inicio():
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    resumen = obtener_resumen_periodo(inicio_semana, hoy)
    bajo = productos_bajo_minimo()
    movs = ultimos_movimientos(8)
    historial = historial_semanas(6)

    return render_template(
        "index.html",
        resumen=resumen,
        bajo_minimo=bajo[:5],
        movimientos=movs,
        historial=historial,
        rol=session.get("rol"),
        nombre=session.get("nombre"),
    )


# ───────────────────────── Inventario ─────────────────────────

@app.route("/inventario")
@login_requerido
def inventario():
    pagina = request.args.get("pagina", 1, type=int)
    busqueda = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()
    por_pagina = 20

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        where = ["activo = 1"]
        params = []
        if busqueda:
            where.append("(codigo LIKE %s OR descripcion LIKE %s)")
            params.extend([f"%{busqueda}%", f"%{busqueda}%"])
        if categoria:
            where.append("categoria = %s")
            params.append(categoria)

        where_sql = " AND ".join(where)

        cursor.execute(f"SELECT COUNT(*) AS total FROM productos WHERE {where_sql}", params)
        total = cursor.fetchone()["total"]
        total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
        pagina = min(max(1, pagina), total_paginas)
        offset = (pagina - 1) * por_pagina

        cursor.execute(f"""
            SELECT id, codigo, descripcion, categoria, unidad, almacen,
                   stock_actual, stock_minimo, stock_maximo, precio_venta
            FROM productos
            WHERE {where_sql}
            ORDER BY descripcion
            LIMIT %s OFFSET %s
        """, params + [por_pagina, offset])
        productos = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT categoria FROM productos
            WHERE categoria IS NOT NULL AND categoria != '' AND activo = 1
            ORDER BY categoria
        """)
        categorias = [r["categoria"] for r in cursor.fetchall()]

        return render_template(
            "inventario.html",
            productos=productos,
            categorias=categorias,
            pagina=pagina,
            total_paginas=total_paginas,
            total=total,
            busqueda=busqueda,
            categoria_sel=categoria,
            rol=session.get("rol"),
            nombre=session.get("nombre"),
        )
    finally:
        cursor.close()
        conexion.close()


@app.route("/productos/nuevo", methods=["GET", "POST"])
@login_requerido
@administrador_requerido
def nuevo_producto():
    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        categoria = request.form.get("categoria", "").strip()
        unidad = request.form.get("unidad", "").strip()
        almacen = request.form.get("almacen", "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        def num(name, default=0):
            try:
                return int(request.form.get(name) or default)
            except (TypeError, ValueError):
                return default

        def decimal(name, default=0.0):
            try:
                return float(request.form.get(name) or default)
            except (TypeError, ValueError):
                return default

        stock_actual = num("stock_actual")
        stock_minimo = num("stock_minimo")
        stock_maximo = num("stock_maximo")
        precio_venta = decimal("precio_venta")

        if not codigo or not descripcion:
            flash("Código y descripción son obligatorios.", "error")
            return redirect(url_for("nuevo_producto"))

        conexion = conectar_db()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                INSERT INTO productos
                    (codigo, descripcion, categoria, unidad, almacen,
                     stock_actual, stock_minimo, stock_maximo, precio_venta, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                codigo, descripcion, categoria or None, unidad or None,
                almacen or None, stock_actual, stock_minimo, stock_maximo,
                precio_venta, observaciones or None
            ))
            conexion.commit()
            flash("Producto registrado correctamente.", "success")
            return redirect(url_for("inventario"))
        except Exception as e:
            conexion.rollback()
            flash(f"No se pudo registrar el producto: {e}", "error")
        finally:
            cursor.close()
            conexion.close()

    return render_template(
        "nuevo_producto.html",
        rol=session.get("rol"),
        nombre=session.get("nombre"),
    )


@app.route("/productos/editar/<int:producto_id>", methods=["GET", "POST"])
@login_requerido
@administrador_requerido
def editar_producto(producto_id):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        if request.method == "POST":
            codigo = request.form.get("codigo", "").strip()
            descripcion = request.form.get("descripcion", "").strip()
            categoria = request.form.get("categoria", "").strip()
            unidad = request.form.get("unidad", "").strip()
            almacen = request.form.get("almacen", "").strip()
            observaciones = request.form.get("observaciones", "").strip()

            def num(name, default=0):
                try:
                    return int(request.form.get(name) or default)
                except (TypeError, ValueError):
                    return default

            def decimal(name, default=0.0):
                try:
                    return float(request.form.get(name) or default)
                except (TypeError, ValueError):
                    return default

            cursor.execute("""
                UPDATE productos SET
                    codigo = %s, descripcion = %s, categoria = %s,
                    unidad = %s, almacen = %s,
                    stock_minimo = %s, stock_maximo = %s,
                    precio_venta = %s, observaciones = %s
                WHERE id = %s
            """, (
                codigo, descripcion, categoria or None, unidad or None,
                almacen or None, num("stock_minimo"), num("stock_maximo"),
                decimal("precio_venta"), observaciones or None, producto_id
            ))
            conexion.commit()
            flash("Producto actualizado.", "success")
            return redirect(url_for("inventario"))

        cursor.execute("SELECT * FROM productos WHERE id = %s", (producto_id,))
        producto = cursor.fetchone()
        if not producto:
            flash("Producto no encontrado.", "error")
            return redirect(url_for("inventario"))

        return render_template(
            "editar_producto.html",
            producto=producto,
            rol=session.get("rol"),
            nombre=session.get("nombre"),
        )
    finally:
        cursor.close()
        conexion.close()


# ───────────────────────── Movimientos ─────────────────────────

@app.route("/movimientos/nuevo", methods=["GET", "POST"])
@login_requerido
@administrador_requerido
def nuevo_movimiento():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        if request.method == "POST":
            producto_id = request.form.get("producto_id", type=int)
            tipo = request.form.get("tipo", "").strip().lower()
            cantidad = request.form.get("cantidad", type=int)
            observaciones = request.form.get("observaciones", "").strip()

            if not producto_id or tipo not in ("entrada", "salida") or not cantidad or cantidad <= 0:
                flash("Datos inválidos.", "error")
                return redirect(url_for("nuevo_movimiento"))

            cursor.execute("SELECT id, stock_actual FROM productos WHERE id = %s", (producto_id,))
            prod = cursor.fetchone()
            if not prod:
                flash("Producto no encontrado.", "error")
                return redirect(url_for("nuevo_movimiento"))

            nuevo_stock = prod["stock_actual"] + cantidad if tipo == "entrada" else prod["stock_actual"] - cantidad
            if nuevo_stock < 0:
                flash("Stock insuficiente para esta salida.", "error")
                return redirect(url_for("nuevo_movimiento"))

            cursor.execute("""
                INSERT INTO movimientos
                    (producto_id, tipo, cantidad, responsable_id, observaciones, origen)
                VALUES (%s, %s, %s, %s, %s, 'manual')
            """, (producto_id, tipo, cantidad, session["usuario_id"], observaciones or None))

            cursor.execute(
                "UPDATE productos SET stock_actual = %s WHERE id = %s",
                (nuevo_stock, producto_id)
            )
            conexion.commit()
            flash("Movimiento registrado correctamente.", "success")
            return redirect(url_for("inventario"))

        cursor.execute("""
            SELECT id, codigo, descripcion, stock_actual
            FROM productos WHERE activo = 1 ORDER BY descripcion
        """)
        productos = cursor.fetchall()
        return render_template(
            "nuevo_movimiento.html",
            productos=productos,
            rol=session.get("rol"),
            nombre=session.get("nombre"),
        )
    except Exception as e:
        if conexion:
            conexion.rollback()
        app.logger.exception("Error movimiento")
        flash("Error al registrar movimiento.", "error")
        return redirect(url_for("inventario"))
    finally:
        cursor.close()
        conexion.close()


# ───────────────────────── Estadísticas ─────────────────────────

@app.route("/estadisticas")
@login_requerido
def estadisticas():
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    resumen = obtener_resumen_periodo(inicio_semana, hoy)
    historial = historial_semanas(12)
    bajo = productos_bajo_minimo()
    movs = ultimos_movimientos(15, inicio_semana, hoy)

    return render_template(
        "estadisticas.html",
        resumen=resumen,
        historial=historial,
        bajo_minimo=bajo,
        movimientos=movs,
        inicio_semana=inicio_semana,
        hoy=hoy,
        rol=session.get("rol"),
        nombre=session.get("nombre"),
    )


@app.route("/estadisticas/generar-snapshot", methods=["POST"])
@login_requerido
@administrador_requerido
def generar_snapshot():
    try:
        generar_snapshot_semanal()
        flash("Snapshot semanal generado correctamente.", "success")
    except Exception as e:
        flash(f"Error al generar snapshot: {e}", "error")
    return redirect(url_for("estadisticas"))


# ───────────────────────── Reportes PDF ─────────────────────────

@app.route("/reportes")
@login_requerido
def reportes():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT r.*, u.nombre AS generador
            FROM reportes_pdf r
            LEFT JOIN usuarios u ON u.id = r.generado_por
            ORDER BY r.creado_en DESC
            LIMIT 30
        """)
        lista = cursor.fetchall()
    except Exception:
        lista = []
    finally:
        cursor.close()
        conexion.close()

    return render_template(
        "reportes.html",
        reportes=lista,
        rol=session.get("rol"),
        nombre=session.get("nombre"),
    )


@app.route("/reportes/generar", methods=["POST"])
@login_requerido
@administrador_requerido
def generar_reporte():
    tipo = request.form.get("tipo", "semanal")
    hoy = date.today()

    if tipo == "semanal":
        inicio = hoy - timedelta(days=hoy.weekday())
        fin = hoy
        label = f"Semana {hoy.isocalendar()[1]} — {inicio.strftime('%d/%m')} al {fin.strftime('%d/%m/%Y')}"
    elif tipo == "quincenal":
        if hoy.day <= 15:
            inicio = hoy.replace(day=1)
            fin = hoy.replace(day=15)
        else:
            inicio = hoy.replace(day=16)
            fin = hoy
        label = f"Quincena {inicio.strftime('%d/%m')} - {fin.strftime('%d/%m/%Y')}"
    else:  # mensual
        inicio = hoy.replace(day=1)
        fin = hoy
        label = inicio.strftime("%B %Y").capitalize()

    resumen = obtener_resumen_periodo(inicio, fin)
    bajo = productos_bajo_minimo()
    movs = ultimos_movimientos(40, inicio, fin)

    datos = {
        "resumen": resumen,
        "bajo_minimo": bajo,
        "movimientos": movs,
    }

    try:
        filename, filepath = generar_reporte_inventario(datos, tipo=tipo, periodo_label=label)

        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO reportes_pdf (tipo, periodo, archivo, generado_por)
            VALUES (%s, %s, %s, %s)
        """, (tipo, label, filename, session["usuario_id"]))
        conexion.commit()
        cursor.close()
        conexion.close()

        flash(f"Reporte {tipo} generado correctamente.", "success")
        return redirect(url_for("reportes"))
    except Exception as e:
        app.logger.exception("Error PDF")
        flash(f"Error al generar PDF: {e}", "error")
        return redirect(url_for("reportes"))


@app.route("/reportes/descargar/<filename>")
@login_requerido
def descargar_reporte(filename):
    # Seguridad básica
    if ".." in filename or "/" in filename or "\\" in filename:
        flash("Archivo no válido.", "error")
        return redirect(url_for("reportes"))

    path = os.path.join(os.path.dirname(__file__), "reports", filename)
    if not os.path.isfile(path):
        flash("Archivo no encontrado.", "error")
        return redirect(url_for("reportes"))

    return send_file(path, as_attachment=True, download_name=filename)


# ───────────────────────── Gestión de empleados ─────────────────────────

@app.route("/empleados")
@login_requerido
@administrador_requerido
def empleados():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, nombre, usuario, rol, activo, creado_en
            FROM usuarios
            ORDER BY rol, nombre
        """)
        users = cursor.fetchall()
        return render_template(
            "empleados.html",
            usuarios=users,
            rol=session.get("rol"),
            nombre=session.get("nombre"),
        )
    finally:
        cursor.close()
        conexion.close()


@app.route("/empleados/nuevo", methods=["GET", "POST"])
@login_requerido
@administrador_requerido
def nuevo_empleado():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")
        rol = request.form.get("rol", "empleado")

        if not nombre or not usuario or len(password) < 8:
            flash("Nombre, usuario y contraseña (mín. 8 caracteres) son obligatorios.", "error")
            return redirect(url_for("nuevo_empleado"))

        if rol not in ("administrador", "empleado"):
            rol = "empleado"

        conexion = conectar_db()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                INSERT INTO usuarios (nombre, usuario, password_hash, rol)
                VALUES (%s, %s, %s, %s)
            """, (nombre, usuario, generate_password_hash(password), rol))
            conexion.commit()
            flash(f"Usuario '{usuario}' creado correctamente.", "success")
            return redirect(url_for("empleados"))
        except Exception as e:
            conexion.rollback()
            flash(f"No se pudo crear el usuario (¿usuario duplicado?): {e}", "error")
        finally:
            cursor.close()
            conexion.close()

    return render_template(
        "nuevo_empleado.html",
        rol=session.get("rol"),
        nombre=session.get("nombre"),
    )


@app.route("/empleados/toggle/<int:user_id>", methods=["POST"])
@login_requerido
@administrador_requerido
def toggle_empleado(user_id):
    if user_id == session["usuario_id"]:
        flash("No puedes desactivar tu propia cuenta.", "error")
        return redirect(url_for("empleados"))

    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE usuarios SET activo = NOT activo WHERE id = %s", (user_id,))
        conexion.commit()
        flash("Estado del usuario actualizado.", "success")
    except Exception:
        conexion.rollback()
        flash("Error al actualizar.", "error")
    finally:
        cursor.close()
        conexion.close()
    return redirect(url_for("empleados"))


# ───────────────────────── Inicialización ─────────────────────────

def asegurar_admin_inicial():
    """Crea un admin por defecto si no existe ninguno."""
    try:
        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS c FROM usuarios WHERE rol = 'administrador'")
        if cursor.fetchone()["c"] == 0:
            cursor.execute("""
                INSERT INTO usuarios (nombre, usuario, password_hash, rol)
                VALUES (%s, %s, %s, 'administrador')
            """, (
                "Administrador Principal",
                "admin",
                generate_password_hash("AdminEmpros2026!"),
            ))
            conexion.commit()
            app.logger.info("Admin inicial creado: admin / AdminEmpros2026!")
        cursor.close()
        conexion.close()
    except Exception as e:
        app.logger.warning(f"No se pudo verificar admin inicial: {e}")


if __name__ == "__main__":
    # Esperar un poco a que MySQL esté listo en Docker
    import time
    for i in range(15):
        try:
            asegurar_admin_inicial()
            break
        except Exception:
            time.sleep(2)

    app.run(host="0.0.0.0", port=5001, debug=True)
