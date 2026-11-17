from pathlib import Path
from decimal import Decimal, InvalidOperation
from openpyxl import load_workbook

from config import conectar_db


def texto(valor):
    if valor is None:
        return None
    resultado = str(valor).strip()
    return resultado if resultado else None


def numero(valor):
    if valor is None or str(valor).strip() == "":
        return None

    try:
        limpio = str(valor).strip().replace("$", "").replace(",", "")
        return Decimal(limpio)
    except (InvalidOperation, ValueError):
        raise ValueError(f"Cantidad invalida: {valor}")


def entero_stock(valor, fila, campo):
    cantidad = numero(valor)

    if cantidad is None:
        return 0

    if cantidad != cantidad.to_integral_value():
        raise ValueError(
            f"Fila {fila}: {campo} debe ser un numero entero: {valor}"
        )

    cantidad = int(cantidad)

    if cantidad < 0:
        raise ValueError(f"Fila {fila}: {campo} no puede ser negativo")

    return cantidad


def importar_productos():

    carpeta = Path(__file__).parent / "database"
    archivos = list(carpeta.glob("*.xlsx"))

    if len(archivos) != 1:
        print("ERROR: Debe existir exactamente un Excel en database.")
        return

    productos = []
    errores = []
    codigos = set()
    pendientes = 0

    libro = load_workbook(
        archivos[0],
        read_only=True,
        data_only=True
    )

    try:
        if "PRODUCTOS" not in libro.sheetnames:
            print("ERROR: No existe la hoja PRODUCTOS.")
            return

        hoja = libro["PRODUCTOS"]

        for n, fila in enumerate(
            hoja.iter_rows(min_row=3, values_only=True),
            start=3
        ):

            fila = tuple(fila) + (None,) * max(0, 11 - len(fila))

            codigo = texto(fila[0])
            descripcion = texto(fila[1])

            if not codigo and not descripcion:
                continue

            if not descripcion:
                errores.append(f"Fila {n}: falta descripcion")
                continue

            if not codigo:
                codigo = f"PEND-{n}"
                print(f"Fila {n}: codigo provisional {codigo}")

            if codigo in codigos:
                errores.append(f"Fila {n}: codigo duplicado {codigo}")
                continue

            codigos.add(codigo)

            try:
                stock_minimo = entero_stock(fila[5], n, "stock minimo")
                stock_maximo = entero_stock(fila[6], n, "stock maximo")
                stock_actual = entero_stock(fila[7], n, "stock actual")

                precio_venta = numero(fila[8])

                if precio_venta is not None and precio_venta < 0:
                    raise ValueError("El precio no puede ser negativo")

            except ValueError as error:
                errores.append(str(error))
                continue

            if fila[7] is None or str(fila[7]).strip() == "":
                pendientes += 1
                print(
                    f"Fila {n}: inventario pendiente; "
                    "se asignara 0 provisional"
                )

            productos.append((
                codigo,
                descripcion,
                texto(fila[3]),
                texto(fila[2]),
                texto(fila[4]),
                stock_actual,
                stock_minimo,
                stock_maximo,
                precio_venta,
                texto(fila[10])
            ))

    finally:
        libro.close()

    print("\n========== GRUPO EMPROS ==========")
    print("Productos preparados:", len(productos))
    print("Inventarios pendientes:", pendientes)
    print("Errores encontrados:", len(errores))

    for error in errores:
        print("-", error)

    if errores or not productos:
        print("\nIMPORTACION CANCELADA. Corrige los errores.")
        return

    conexion = None
    cursor = None

    try:
        conexion = conectar_db()
        cursor = conexion.cursor()

        cursor.execute("SELECT COUNT(*) FROM productos")
        existentes = cursor.fetchone()[0]

        if existentes > 0:
            print(
                f"\nIMPORTACION CANCELADA: "
                f"ya existen {existentes} productos."
            )
            return

        print("\nSe van a importar", len(productos), "productos.")
        print("Los inventarios pendientes se guardaran como cero provisional.")

        confirmacion = input(
            "\nEscribe IMPORTAR para confirmar: "
        ).strip()

        if confirmacion != "IMPORTAR":
            print("Operacion cancelada.")
            return

        sql = """
            INSERT INTO productos (
                codigo,
                descripcion,
                categoria,
                unidad,
                almacen,
                stock_actual,
                stock_minimo,
                stock_maximo,
                precio_venta,
                observaciones,
                activo,
                creado_en,
                actualizado_en
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                1, NOW(), NOW()
            )
        """

        cursor.executemany(sql, productos)

        conexion.commit()

        print("\n================================")
        print("IMPORTACION EXITOSA")
        print("Productos importados:", cursor.rowcount)
        print("Inventarios pendientes:", pendientes)
        print("================================")

    except Exception as error:
        if conexion:
            conexion.rollback()

        print("\nERROR AL IMPORTAR:", error)
        print("Se revirtieron los cambios de esta importacion.")

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()


if __name__ == "__main__":
    importar_productos()
