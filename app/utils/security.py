from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

# Configuración JWT
SECRET_KEY = os.getenv(
    "SECRET_KEY", "secretkeysecret"
)  # En producción usar una clave segura
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE", "30"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token JWT"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE)

    # Convertir user_id a string para el campo 'sub'
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verificar y decodificar token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"Error verificando token: {e}")  # Para debug
        return None


def extract_user_from_token(token: str) -> Optional[dict]:
    """Extraer información del usuario desde el token"""
    payload = verify_token(token)
    if payload is None:
        print("Payload es None")  # Debug
        return None

    # Extraer datos del token
    user_id_str = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")

    print(
        f"Datos extraidos del token - user_id_str: {user_id_str}, email: {email}, role: {role}"
    )  # Debug

    # Validar y convertir user_id a entero
    if user_id_str is None:
        print("user_id_str es None")  # Debug
        return None

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        print(f"No se pudo convertir user_id a entero: {user_id_str}")  # Debug
        return None

    return {"user_id": user_id, "email": email, "role": role}