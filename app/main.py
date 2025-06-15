# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .views import usuario_routes
from .models.database import test_connection, create_tables


# Cargar variables de entorno
load_dotenv()


# Verificar conexión a MySQL antes de iniciar
if not test_connection():
    raise Exception("No se pudo conectar a MySQL. Verifica tu configuración.")

# Crear todas las tablas
create_tables()

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Autenticación FastAPI",
    description="API REST con autenticación JWT y gestión de usuarios",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(usuario_routes.router, prefix="/api/v1")


# Ruta raíz
@app.get("/")
def root():
    return {
        "mensaje": "Sistema de Autenticación FastAPI",
        "version": "1.0.0",
        "docs": "/docs",
        "database": "MySQL conectado ✅",
        "endpoints": {
            "register": "POST /api/v1/auth/register",
            "login": "POST /api/v1/auth/login",
            "profile": "GET /api/v1/auth/profile",
            "change_password": "PATCH /api/v1/auth/change-password",
            "users": "GET /api/v1/auth/users (admin only)",
        },
    }


# Health check con verificación de DB
@app.get("/health")
def health_check():
    db_status = "connected" if test_connection() else "disconnected"
    return {
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0",
        "auth": "JWT enabled",
    }
