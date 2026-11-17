
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from collections import Counter
from openpyxl import load_workbook

from config import conectar_db


def texto(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor if valor else None


def codigo_normalizado(valor):
    if valor is None:
        return None

    if isinstance(valor, (int, float, Decimal)):
        numero = Decimal(str(valor))
        if numero == numero.to_integral_value():
            return str(int(numero))

    return texto(valor)


def cantidad(valor):
    if valor is None or str(valor).strip() == "":
        return None

    try:
        return Decimal(str(valor).strip())
    except (InvalidOperation, ValueError):
        raise ValueError("Cantidad no numérica")


def fecha_normalizada(valor):
    if isinstance(valor, datetime):
        return valor

    if isinstance(valor, date):
        return datetime.combine(valor, datetime.min.time())

    return None


def importar():
    carpeta = Path(__file__).parent / "database"
    archivos = list(carpeta.glob("*.xlsx"))

    if len(archivos) != 1:
        print("Debe existir exactamente un archivo Excel.")
        return

    libro = load_workbook(
        archivos[0],
        read_only=True,
        data_only=True
    )

    conexion = None
    cursor = None

    try:
        hoja = libro["REGISTRO Entradas - Salidas"]

        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT id, codigo FROM productos")
        productos = {
            str(p["codigo"]).strip(): p["id"]
            for p in cursor.fetchall()
        }

        cursor.execute("""
            SELECT id
            FROM usuarios
            WHERE rol = 'administrador' AND activo = 1
            ORDER BY id
            LIMIT 1
        """)
        administrador = cursor.fetchone()

        if not administrador:
            print("No existe un administrador activo.")
            return

        responsable_id = administrador["id"]

        cursor.execute("SELECT COUNT(*) AS total FROM movimientos")
        total_movimientos = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM movimientos_pendientes"
        )
        total_pendientes = cursor.fetchone()["total"]

        if total_movimientos or total_pendientes:
            print("Ya existen movimientos o pendientes.")
            print("Importación cancelada para evitar duplicados.")
            return

        movimientos = []
        pendientes = []
        estadisticas = Counter()

        for n, fila in enumerate(
            hoja.iter_rows(min_row=3, values_only=True),
            start=3
        ):
            if all(v is None for v in fila[:11]):
                continue

            codigo = codigo_normalizado(fila[1])
            descripcion = texto(fila[2])
            fecha = fecha_normalizada(fila[0])

            try:
                entrada = cantidad(fila[4])
                salida = cantidad(fila[5])
                error_cantidad = False
            except ValueError:
                entrada = None
                salida = None
                error_cantidad = True

            tipo_salida = texto(fila[6])
            entregado_a = texto(fila[7])
            proveedor = texto(fila[8])
            cliente = texto(fila[9])
            observaciones = texto(fila[10])

            # Filas auxiliares del Excel, sin movimiento real.
            if (
                descripcion in (None, "#N/A")
                and entrada is None
                and salida is None
                and not error_cantidad
            ):
                estadisticas["auxiliares"] += 1
                continue

            motivos = []

            if error_cantidad:
                motivos.append("Cantidad no numérica")

            if fecha is None:
                motivos.append("Fecha faltante o inválida")

            if codigo not in productos:
                motivos.append("Producto no encontrado")

            tiene_entrada = entrada is not None and entrada > 0
            tiene_salida = salida is not None and salida > 0

            if tiene_entrada and tiene_salida:
                motivos.append("Entrada y salida simultáneas")
            elif not tiene_entrada and not tiene_salida:
                motivos.append("Sin cantidad positiva")

            if (
                (entrada is not None and entrada < 0)
                or (salida is not None and salida < 0)
            ):
                motivos.append("Cantidad negativa")

            if motivos:
                pendientes.append((
                    n,
                    fecha,
                    codigo,
                    descripcion,
                    entrada,
                    salida,
                    tipo_salida,
                    entregado_a,
                    proveedor,
                    cliente,
                    observaciones,
                    "; ".join(motivos)
                ))
                estadisticas["pendientes"] += 1
                continue

            if tiene_entrada:
                tipo = "entrada"
                valor = entrada
                estadisticas["entradas"] += 1
            else:
                tipo = "salida"
                valor = salida
                estadisticas["salidas"] += 1

            movimientos.append((
                productos[codigo],
                tipo,
                valor,
                responsable_id,
                entregado_a,
                proveedor,
                cliente,
                observaciones,
                fecha,
                tipo_salida,
                entregado_a,
                fecha
            ))

        print("\n=== GRUPO EMPROS ===")
        print("RESUMEN DE IMPORTACIÓN\n")
        print("Entradas válidas:", estadisticas["entradas"])
        print("Salidas válidas:", estadisticas["salidas"])
        print("Pendientes:", estadisticas["pendientes"])
        print("Filas auxiliares:", estadisticas["auxiliares"])
        print("Total de movimientos válidos:", len(movimientos))

        print(
            "\nEl stock actual de productos NO será modificado."
        )

        if not movimientos and not pendientes:
            print("No hay registros para importar.")
            return

        confirmacion = input(
            "\nEscribe IMPORTAR para guardar: "
        ).strip()

        if confirmacion != "IMPORTAR":
            print("Operación cancelada.")
            return

       # La transacción ya está activa por las consultas anteriores.
# No es necesario iniciar otra.

        if movimientos:
            cursor.executemany("""
                INSERT INTO movimientos (
                    producto_id,
                    tipo,
                    cantidad,
                    responsable_id,
                    persona_recibe,
                    proveedor,
                    cliente,
                    observaciones,
                    fecha,
                    tipo_salida,
                    entregado_a,
                    fecha_original
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
            """, movimientos)

        if pendientes:
            cursor.executemany("""
                INSERT INTO movimientos_pendientes (
                    fila_excel,
                    fecha_original,
                    codigo_original,
                    descripcion,
                    entrada,
                    salida,
                    tipo_salida,
                    entregado_a,
                    proveedor,
                    cliente,
                    observaciones,
                    motivo
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
            """, pendientes)

        conexion.commit()

        print("\nIMPORTACIÓN EXITOSA")
        print("Movimientos importados:", len(movimientos))
        print("Movimientos pendientes:", len(pendientes))

    except Exception as error:
        if conexion:
            conexion.rollback()
        print("\nERROR:", error)
        print("No se guardaron cambios de esta operación.")

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()
        libro.close()


if __name__ == "__main__":
    importar()
