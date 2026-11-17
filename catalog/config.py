import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

def conectar_db():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "db"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "empros"),
            password=os.getenv("DB_PASSWORD", "emprospass"),
            database=os.getenv("DB_NAME", "grupo_empros"),
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
        )
    except Error as e:
        raise ConnectionError(f"Error de conexion: {e}")
