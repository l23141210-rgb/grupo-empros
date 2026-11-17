
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
        return Decimal(str(valor).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Cantidad inválida: {valor}")


def importar_productos():
    carpeta = Path(__file__).parent / "database"
    archivos = list(carpeta.glob("*.xlsx"))

    if len(archivos) != 1:
        print("ERROR: Debe existir exactamente un Excel en database.")
        return

    libro = load_workbook(archivos[0], read_only=True, data_only=True)
    productos = []
    errores = []
    codigos = set()

    try:
        hoja = libro["PRODUCTOS"]

        for n, fila in enumerate(
            hoja.iter_rows(min_row=3, values_only=True), start=3
        ):
            codigo = texto(fila[0])
            descripcion = texto(fila[1])

            if not codigo and not descripcion:
                continue

            if not descripcion:
                errores.append(f"Fila {n}: falta descripción.")
                continue

            if not codigo:
                codigo = f"PEND-{n}"
                print(f"Fila {n}: código provisional {codigo}")

            if codigo in codigos:
                errores.append(f"Fila {n}: código duplicado {codigo}")
                continue

            codigos.add(codigo)

            try:
                stock_minimo = numero(fila[5])
                stock_maximo = numero(fila[6])
                stock_actual = numero(fila[7])
                precio_venta = numero(fila[8])
            except ValueError as error:
                errores.append(f"Fila {n}: {error}")
                continue

           if stock_actual is None:
    print(f"Fila {n}: inventario pendiente, se asignará 0 provisional")
    stock_actual = 0

            productos.append((
                codigo,
                descripcion,
                texto(fila[3]),
                texto(fila[2]),
                texto(fila[4]),
                stock_actual,
                stock_minimo if stock_minimo is not None else 0,
                stock_maximo if stock_maximo is not None else 0,
                precio_venta,
                texto(fila[10])
            ))

    finally:
        libro.close()

    print("\n=== GRUPO EMPROS ===")
    print("Productos preparados:", len(productos))
    print("Errores encontrados:", len(errores))

    for error in errores[:30]:
        print("-", error)

    if errores or not productos:
        print("Importación cancelada.")
        return

    conexion = None
    cursor = None

    try:
        conexion = conectar_db()
        cursor = conexion.cursor()

        cursor.execute("SELECT COUNT(*) FROM productos")
        existentes = cursor.fetchone()[0]

        if existentes > 0:
            print("La tabla ya contiene productos. No se importará.")
            return

        confirmacion = input(
            "\nEscribe IMPORTAR para guardar: "
        ).strip()

        if confirmacion != "IMPORTAR":
            print("Operación cancelada.")
            return

        cursor.executemany("""
            INSERT INTO productos (
                codigo, descripcion, categoria, unidad, almacen,
                stock_actual, stock_minimo, stock_maximo,
                precio_venta, observaciones
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, productos)

        conexion.commit()

        print("\nIMPORTACIÓN EXITOSA")
        print("Productos importados:", len(productos))

    except Exception as error:
        if conexion:
            conexion.rollback()
        print("ERROR:", error)

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()


if __name__ == "__main__":
    importar_productos()


