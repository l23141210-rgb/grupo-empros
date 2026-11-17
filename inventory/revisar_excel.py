
from pathlib import Path
from openpyxl import load_workbook

carpeta = Path(__file__).parent / "database"
archivos = list(carpeta.glob("*.xlsx"))

if not archivos:
    print("ERROR: No se encontró ningún Excel en database.")
else:
    archivo = archivos[0]
    libro = load_workbook(archivo, read_only=True, data_only=True)

    print("GRUPO EMPROS - REVISIÓN DEL EXCEL")
    print("Archivo:", archivo.name)

    for hoja in libro:
        print(f"\nHoja: {hoja.title}")
        print(f"Filas: {hoja.max_row}")
        print(f"Columnas: {hoja.max_column}")

        print("Primeras 5 filas:")
        for fila in hoja.iter_rows(
            min_row=1,
            max_row=min(5, hoja.max_row),
            values_only=True
        ):
            print(fila)

    libro.close()
