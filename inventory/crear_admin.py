
from getpass import getpass

from mysql.connector import Error
from werkzeug.security import generate_password_hash

from config import conectar_db


def crear_administrador():
    print("\n=== GRUPO EMPROS ===")
    print("Registro de administrador\n")

    nombre = input("Nombre completo: ").strip()
    usuario = input("Nombre de usuario: ").strip()
    password = getpass("Contraseña (mínimo 12 caracteres): ")

    if not nombre or not usuario or len(password) < 12:
        print("Datos inválidos. La contraseña debe tener al menos 12 caracteres.")
        return

    conexion = None
    cursor = None

    try:
        conexion = conectar_db()
        conexion.start_transaction()

        cursor = conexion.cursor()

        # Bloquea la tabla de control durante el registro.
        cursor.execute("""
            SELECT GET_LOCK('grupo_empros_admin', 10)
        """)
        bloqueo = cursor.fetchone()[0]

        if bloqueo != 1:
            print("No se pudo obtener el bloqueo de seguridad.")
            conexion.rollback()
            return

        cursor.execute("""
            SELECT COUNT(*)
            FROM usuarios
            WHERE rol = 'administrador'
        """)

        total = cursor.fetchone()[0]

        if total >= 3:
            print("Ya existen tres administradores.")
            conexion.rollback()
            return

        cursor.execute("""
            INSERT INTO usuarios
                (nombre, usuario, password_hash, rol)
            VALUES (%s, %s, %s, 'administrador')
        """, (
            nombre,
            usuario,
            generate_password_hash(password)
        ))

        conexion.commit()
        print("Administrador registrado correctamente.")

    except Error as error:
        if conexion:
            conexion.rollback()
        print("No se pudo crear el administrador:", error)

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            try:
                cursor_bloqueo = conexion.cursor()
                cursor_bloqueo.execute(
                    "SELECT RELEASE_LOCK('grupo_empros_admin')"
                )
                cursor_bloqueo.close()
            except Error:
                pass

            conexion.close()


if __name__ == "__main__":
    crear_administrador()
