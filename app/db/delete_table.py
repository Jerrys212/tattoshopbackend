from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

# Cargar variables de entorno
load_dotenv()

# Configuración de MySQL
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "tatuajes")

# Crear conexión
if MYSQL_PASSWORD:
    DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
else:
    DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine = create_engine(DATABASE_URL)

# Nombre de la tabla que quieres borrar
TABLA_A_BORRAR = "users"  # Cambia por el nombre de tu tabla

def borrar_tabla():
    try:
        with engine.connect() as connection:
            # Verificar si la tabla existe
            result = connection.execute(text(f"SHOW TABLES LIKE '{TABLA_A_BORRAR}'"))
            if result.fetchone():
                # Borrar la tabla
                connection.execute(text(f"DROP TABLE {TABLA_A_BORRAR}"))
                connection.commit()
                print(f"✅ Tabla '{TABLA_A_BORRAR}' eliminada exitosamente")
            else:
                print(f"❌ La tabla '{TABLA_A_BORRAR}' no existe")
    except Exception as e:
        print(f"❌ Error al eliminar la tabla: {e}")

if __name__ == "__main__":
    confirmacion = input(f"¿Estás seguro de que quieres borrar la tabla '{TABLA_A_BORRAR}'? (si/no): ")
    if confirmacion.lower() in ['si', 'sí', 'yes', 'y']:
        borrar_tabla()
    else:
        print("Operación cancelada")