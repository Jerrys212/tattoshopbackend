from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.usuario import User, UserRole
from ..utils.security import extract_user_from_token

# Configurar Bearer Token
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
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
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if user is None:
        print(f"Usuario no encontrado con ID: {token_data['user_id']}")  # Debug
        raise credentials_exception

    print(f"Usuario encontrado: {user.email}, confirmado: {user.email_confirmed}")  # Debug

    # Verificar que el email esté confirmado
    if not user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Debes confirmar tu email antes de acceder"
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Obtener usuario activo (verificación adicional)"""
    if not current_user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Email no confirmado"
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Requerir permisos de administrador"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Se requiere rol de administrador",
        )
    return current_user


def require_role(required_role: UserRole):
    """Factory para crear dependencia que requiere un rol específico"""

    def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Se requiere rol: {required_role.value}",
            )
        return current_user

    return role_checker


def require_admin_or_artist(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Requerir rol de admin o artist"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ARTIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Se requiere rol de administrador o artista",
        )
    return current_user


def require_admin_or_self(user_id: int):
    """Factory para verificar que sea admin o el mismo usuario"""
    
    def admin_or_self_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role != UserRole.ADMIN and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes acceder a tu propia información o ser administrador",
            )
        return current_user

    return admin_or_self_checker