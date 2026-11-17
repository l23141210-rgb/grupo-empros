
from pathlib import Path
from collections import Counter
from decimal import Decimal, InvalidOperation
from openpyxl import load_workbook

from config import conectar_db


def normalizar_codigo(valor):
    if valor is None:
        return None

    if isinstance(valor, (int, float, Decimal)):
        if Decimal(str(valor)) == int(valor):
            return str(int(valor))

    return str(valor).strip() or None


def cantidad(valor):
    if valor is None or str(valor).strip() == "":
        return None

    try:
        return Decimal(str(valor).strip())
    except (InvalidOperation, ValueError):
        return None


carpeta = Path(__file__).parent / "database"
archivos = list(carpeta.glob("*.xlsx"))

if len(archivos) != 1:
    raise SystemExit(
        "Debe existir exactamente un Excel en database."
    )

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
    cursor = conexion.cursor()

    cursor.execute("SELECT codigo FROM productos")
    codigos_bd = {
        str(fila[0]).strip()
        for fila in cursor.fetchall()
    }

    estadisticas = Counter()
    faltantes = Counter()
    problemas = []

    for n, fila in enumerate(
        hoja.iter_rows(min_row=3, values_only=True),
        start=3
    ):
        fecha = fila[0]
        codigo = normalizar_codigo(fila[1])
        entrada = cantidad(fila[4])
        salida = cantidad(fila[5])

        if all(valor is None for valor in fila[:11]):
            continue

        estadisticas["filas_con_datos"] += 1

        if codigo not in codigos_bd:
            faltantes[codigo or "SIN CODIGO"] += 1

        tiene_entrada = entrada is not None and entrada > 0
        tiene_salida = salida is not None and salida > 0

        if tiene_entrada and tiene_salida:
            problemas.append(
                f"Fila {n}: entrada y salida simultáneas"
            )
        elif tiene_entrada:
            estadisticas["entradas"] += 1
        elif tiene_salida:
            estadisticas["salidas"] += 1
        else:
            problemas.append(
                f"Fila {n}: sin cantidad positiva válida"
            )

        if fecha is None:
            problemas.append(f"Fila {n}: sin fecha")

    print("\n=== GRUPO EMPROS ===")
    print("REVISIÓN DE MOVIMIENTOS\n")

    print("Filas con datos:",
          estadisticas["filas_con_datos"])
    print("Entradas:", estadisticas["entradas"])
    print("Salidas:", estadisticas["salidas"])

    print("\nCódigos no encontrados en MySQL:")
    if faltantes:
        for codigo, total in faltantes.most_common(20):
            print(f"- {codigo}: {total} movimientos")
    else:
        print("Ninguno")

    print("\nProblemas detectados:", len(problemas))
    for problema in problemas[:20]:
        print("-", problema)

    print("\nNo se modificó la base de datos.")

finally:
    if cursor:
        cursor.close()

    if conexion and conexion.is_connected():
        conexion.close()

    libro.close()
