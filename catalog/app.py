import os
from flask import Flask, render_template, request
from config import conectar_db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "catalog-empros-public-key")

WHATSAPP_NUMERO = os.environ.get("WHATSAPP_NUMERO", "5215512345678")
WHATSAPP_MENSAJE = os.environ.get(
    "WHATSAPP_MENSAJE",
    "Hola, vi el catalogo de Grupo Empros y me interesa cotizar materiales."
)

def obtener_productos(busqueda="", categoria="", pagina=1, por_pagina=24):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        where = ["activo = 1", "stock_actual > 0"]
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
            SELECT id, codigo, descripcion, categoria, unidad,
                   stock_actual, precio_venta, almacen
            FROM productos
            WHERE {where_sql}
            ORDER BY descripcion
            LIMIT %s OFFSET %s
        """, params + [por_pagina, offset])
        productos = cursor.fetchall()
        cursor.execute("""
            SELECT DISTINCT categoria FROM productos
            WHERE categoria IS NOT NULL AND categoria != '' AND activo = 1 AND stock_actual > 0
            ORDER BY categoria
        """)
        categorias = [r["categoria"] for r in cursor.fetchall()]
        return productos, categorias, total, pagina, total_paginas
    finally:
        cursor.close()
        conexion.close()

@app.route("/")
def inicio():
    busqueda = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()
    pagina = request.args.get("pagina", 1, type=int)
    try:
        productos, categorias, total, pagina, total_paginas = obtener_productos(busqueda, categoria, pagina)
        error = None
    except Exception:
        productos, categorias, total, pagina, total_paginas = [], [], 0, 1, 1
        error = "No se pudo cargar el catalogo en este momento."
    whatsapp_url = f"https://wa.me/{WHATSAPP_NUMERO}?text={WHATSAPP_MENSAJE.replace(' ', '%20')}"
    return render_template(
        "index.html",
        productos=productos,
        categorias=categorias,
        total=total,
        pagina=pagina,
        total_paginas=total_paginas,
        busqueda=busqueda,
        categoria_sel=categoria,
        whatsapp_url=whatsapp_url,
        error=error,
    )

@app.route("/producto/<int:producto_id>")
def detalle(producto_id):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, codigo, descripcion, categoria, unidad,
                   stock_actual, precio_venta, almacen, observaciones
            FROM productos
            WHERE id = %s AND activo = 1
        """, (producto_id,))
        producto = cursor.fetchone()
        if not producto:
            return "Producto no encontrado", 404
        whatsapp_url = (
            f"https://wa.me/{WHATSAPP_NUMERO}"
            f"?text=Hola,%20me%20interesa%20el%20producto%20{producto['codigo']}"
        )
        return render_template("detalle.html", producto=producto, whatsapp_url=whatsapp_url)
    finally:
        cursor.close()
        conexion.close()

@app.route("/contacto")
def contacto():
    whatsapp_url = f"https://wa.me/{WHATSAPP_NUMERO}?text={WHATSAPP_MENSAJE.replace(' ', '%20')}"
    return render_template("contacto.html", whatsapp_url=whatsapp_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
