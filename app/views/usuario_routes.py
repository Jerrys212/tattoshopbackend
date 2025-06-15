from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException

from ..models.database import get_db
from ..controllers.usuario_controller import AuthController
from ..schemas.usuario_schema import (
    UserCreate,
    UserLogin,
    PasswordUpdate,
    UserResponse,
    LoginResponse,
    UserListItem,
)
from ..utils.auth_dependencies import (
    get_current_active_user,
    require_admin,
)
from ..models.usuario import AuthUser

# Crear router
router = APIRouter(
    prefix="/auth",
    tags=["autenticacion"],
    responses={401: {"description": "No autorizado"}},
)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    # current_user: AuthUser = Depends(require_admin)  # Solo admins pueden crear usuarios
):
    """Crear un nuevo usuario (requiere permisos de admin)"""
    controller = AuthController(db)
    new_user = controller.create_user(user)
    return new_user


@router.post("/login", response_model=LoginResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Iniciar sesión y obtener token"""
    controller = AuthController(db)
    user, access_token = controller.authenticate_user(login_data)

    return LoginResponse(
        access_token=access_token, token_type="bearer", user=user, expires_in=3600
    )


@router.get("/profile", response_model=UserResponse)
def get_my_profile(current_user: AuthUser = Depends(get_current_active_user)):
    """Obtener mi perfil actual"""
    return current_user


@router.get("/profile/{user_id}", response_model=UserResponse)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(
        require_admin
    ),  # Solo admins pueden ver otros perfiles
):
    """Obtener perfil de cualquier usuario (solo admins)"""
    controller = AuthController(db)
    user = controller.get_user_profile(user_id)
    return user


@router.patch("/change-password", response_model=UserResponse)
def change_my_password(
    password_data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_active_user),
):
    """Cambiar mi contraseña"""
    controller = AuthController(db)
    updated_user = controller.update_password(current_user.id, password_data)
    return updated_user


@router.get("/users", response_model=List[UserListItem])
def list_users(
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    is_active: Optional[bool] = Query(None, description="Filtrar por usuarios activos"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(
        require_admin
    ),  # Solo admins pueden listar usuarios
):
    """Listar todos los usuarios (solo admins)"""
    controller = AuthController(db)
    users = controller.get_all_users(skip=skip, limit=limit, is_active=is_active)
    return users


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_admin),
):
    """Desactivar usuario (solo admins)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivarte a ti mismo",
        )

    controller = AuthController(db)
    deactivated_user = controller.deactivate_user(user_id)
    return deactivated_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_admin),
):
    """Eliminar usuario permanentemente (solo admins)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminarte a ti mismo",
        )

    controller = AuthController(db)
    controller.delete_user(user_id)
    return None


# Endpoint para verificar permisos específicos
@router.get("/check-permission/{permission}")
def check_permission(
    permission: str, current_user: AuthUser = Depends(get_current_active_user)
):
    """Verificar si el usuario actual tiene un permiso específico"""
    has_permission = current_user.has_permission(permission)
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "permission": permission,
        "has_permission": has_permission,
    }
