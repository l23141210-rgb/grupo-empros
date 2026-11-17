import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()


def conectar_db():
    """Conexión a MySQL usando variables de entorno (Docker o local)."""
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "empros"),
            password=os.getenv("DB_PASSWORD", "emprospass"),
            database=os.getenv("DB_NAME", "grupo_empros"),
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=False,
        )
        return conexion
    except Error as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos: {e}")
