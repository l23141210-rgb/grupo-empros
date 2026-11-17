
from pathlib import Path
from openpyxl import load_workbook

carpeta = Path(__file__).parent / "database"
archivo = next(carpeta.glob("*.xlsx"))

libro = load_workbook(
    archivo,
    read_only=True,
    data_only=True
)

hoja = libro["PRODUCTOS"]

print("\n=== GRUPO EMPROS ===")
print("REVISIÓN DE FILAS CON ERRORES\n")

for numero in range(85, 101):
    fila = list(
        hoja.iter_rows(
            min_row=numero,
            max_row=numero,
            values_only=True
        )
    )[0]

    print(f"\nFILA {numero}")
    print("Código:", fila[0])
    print("Descripción:", fila[1])
    print("Unidad:", fila[2])
    print("Categoría:", fila[3])
    print("Almacén:", fila[4])
    print("Stock mínimo:", fila[5])
    print("Stock máximo:", fila[6])
    print("Inventario:", fila[7])
    print("Estado:", fila[9])

libro.close()
