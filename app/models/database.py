from sqlalchemy import create_engine, text  # Agregar text import
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Configuración de MySQL
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "tatuajes")

# URL de conexión a MySQL
# Manejar contraseña vacía correctamente
if MYSQL_PASSWORD:
    DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
else:
    DATABASE_URL = (
        f"mysql+pymysql://{MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )

# Crear engine con configuración específica para MySQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verificar conexión antes de usar
    pool_recycle=300,  # Renovar conexiones cada 5 minutos
    echo=True,  # Mostrar queries SQL (quitar en producción)
)

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()


# Dependencia para obtener la sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Función para crear todas las tablas
def create_tables():
    """Crear todas las tablas en la base de datos"""
    Base.metadata.create_all(bind=engine)


# Función para verificar conexión
def test_connection():
    """Probar la conexión a MySQL"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))  # Usar text() aquí
            return True
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False
