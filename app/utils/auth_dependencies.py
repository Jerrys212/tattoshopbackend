from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.usuario import AuthUser
from ..utils.security import extract_user_from_token

# Configurar Bearer Token
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> AuthUser:
    """Obtener usuario actual desde el token JWT"""

    print(
        f"Token recibido: {credentials.credentials[:50]}..."
    )  # Debug (solo primeros 50 chars)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extraer información del token
    token_data = extract_user_from_token(credentials.credentials)
    if token_data is None:
        print("token_data es None - Token inválido")  # Debug
        raise credentials_exception

    print(f"Token data extraída: {token_data}")  # Debug

    # Buscar usuario en base de datos
    user = db.query(AuthUser).filter(AuthUser.id == token_data["user_id"]).first()
    if user is None:
        print(f"Usuario no encontrado con ID: {token_data['user_id']}")  # Debug
        raise credentials_exception

    print(f"Usuario encontrado: {user.username}, activo: {user.is_active}")  # Debug

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo"
        )

    return user


def get_current_active_user(
    current_user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    """Obtener usuario activo (verificación adicional)"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo"
        )
    return current_user


def require_admin(
    current_user: AuthUser = Depends(get_current_active_user),
) -> AuthUser:
    """Requerir permisos de administrador"""
    if not current_user.has_permission("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Se requiere rol de administrador",
        )
    return current_user


def require_permission(permission: str):
    """Factory para crear dependencia que requiere un permiso específico"""

    def permission_checker(
        current_user: AuthUser = Depends(get_current_active_user),
    ) -> AuthUser:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Se requiere permiso: {permission}",
            )
        return current_user

    return permission_checker
