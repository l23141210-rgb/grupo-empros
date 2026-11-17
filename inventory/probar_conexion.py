
from config import conectar_db

try:
    conexion = conectar_db()

    if conexion.is_connected():
        print("CONEXIÓN EXITOSA A GRUPO EMPROS")

        cursor = conexion.cursor()
        cursor.execute("SHOW TABLES")

        print("\nTablas encontradas:")

        for tabla in cursor.fetchall():
            print("-", tabla[0])

        cursor.close()
        conexion.close()

except Exception as error:
    print("ERROR DE CONEXIÓN:", error)
