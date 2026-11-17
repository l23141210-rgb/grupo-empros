
from pathlib import Path
from openpyxl import load_workbook

carpeta = Path(__file__).parent / "database"
archivos = list(carpeta.glob("*.xlsx"))

if len(archivos) != 1:
    raise SystemExit("Debe existir exactamente un Excel.")

libro = load_workbook(
    archivos[0],
    read_only=True,
    data_only=True
)

try:
    hoja = libro["REGISTRO Entradas - Salidas"]

    filas = [
        14, 208, 380, 1019, 1097,
        1678, 1679, 1680, 1681,
        1682, 1683, 1684, 1685,
        1686, 1687, 1688
    ]

    print("\n=== GRUPO EMPROS ===")
    print("REVISIÓN DETALLADA\n")

    for n in filas:
        fila = list(
            hoja.iter_rows(
                min_row=n,
                max_row=n,
                values_only=True
            )
        )[0]

        print(f"\nFILA {n}")
        print("Fecha:", fila[0])
        print("Código:", fila[1])
        print("Descripción:", fila[2])
        print("Entrada:", fila[4])
        print("Salida:", fila[5])
        print("Tipo de salida:", fila[6])
        print("Entregado a:", fila[7])
        print("Proveedor:", fila[8])
        print("Cliente:", fila[9])
        print("Observaciones:", fila[10])

    print("\nMOVIMIENTOS CON CÓDIGO NO ENCONTRADO")

    encontrados = 0

    for n, fila in enumerate(
        hoja.iter_rows(min_row=3, values_only=True),
        start=3
    ):
        if str(fila[1]).strip() == "CON-104.5X97.5X51.5":
            print(
                f"Fila {n}: "
                f"Descripción={fila[2]}, "
                f"Entrada={fila[4]}, "
                f"Salida={fila[5]}"
            )
            encontrados += 1

    print("Coincidencias:", encontrados)

finally:
    libro.close()
