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
    EmailConfirmation,
    ResendConfirmation,
    RegisterResponse,
)
from ..utils.auth_dependencies import (
    get_current_active_user,
    require_admin,
    require_admin_or_self,
)
from ..models.usuario import User

# Crear router
router = APIRouter(
    prefix="/auth",
    tags=["autenticacion"],
    responses={401: {"description": "No autorizado"}},
)


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(require_admin)  # Comentado para permitir registro libre
):
    """Crear un nuevo usuario y enviar email de confirmación"""
    controller = AuthController(db)
    new_user = controller.create_user(user)
    return RegisterResponse(
        message="Usuario registrado exitosamente. Revisa tu email para confirmar tu cuenta.",
        user=new_user,
        confirmation_required=True,
    )


@router.post("/confirm-email", response_model=UserResponse)
def confirm_email(confirmation_data: EmailConfirmation, db: Session = Depends(get_db)):
    """Confirmar email del usuario con token alfanumérico"""
    controller = AuthController(db)
    confirmed_user = controller.confirm_email(confirmation_data)
    return confirmed_user


@router.post("/resend-confirmation")
def resend_confirmation_email(
    resend_data: ResendConfirmation, db: Session = Depends(get_db)
):
    """Reenviar email de confirmación"""
    controller = AuthController(db)
    success = controller.resend_confirmation_email(resend_data)

    if success:
        return {
            "message": "Email de confirmación enviado. Revisa tu bandeja de entrada.",
            "success": True,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error enviando email de confirmación. Intenta más tarde.",
        )


@router.post("/login", response_model=LoginResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Iniciar sesión y obtener token (requiere email confirmado)"""
    controller = AuthController(db)
    user, access_token = controller.authenticate_user(login_data)

    return LoginResponse(
        access_token=access_token, token_type="bearer", user=user, expires_in=3600
    )


@router.get("/profile", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_active_user)):
    """Obtener mi perfil actual"""
    return current_user


@router.get("/profile/{user_id}", response_model=UserResponse)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_self(id)),
):
    """Obtener perfil de usuario (solo admins o el mismo usuario)"""
    controller = AuthController(db)
    user = controller.get_user_profile(user_id)
    return user


@router.patch("/change-password", response_model=UserResponse)
def change_my_password(
    password_data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cambiar mi contraseña"""
    controller = AuthController(db)
    updated_user = controller.update_password(current_user.id, password_data)
    return updated_user


@router.get("/users", response_model=List[UserListItem])
def list_users(
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    role: Optional[str] = Query(None, description="Filtrar por rol (admin, client, artist)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # Solo admins pueden listar usuarios
):
    """Listar todos los usuarios (solo admins)"""
    controller = AuthController(db)
    users = controller.get_all_users(skip=skip, limit=limit, role=role)
    return users


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
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


@router.get("/check-role")
def check_my_role(current_user: User = Depends(get_current_active_user)):
    """Verificar mi rol actual"""
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "email_confirmed": current_user.email_confirmed,
    }


@router.get("/confirmation-status/{user_id}")
def get_confirmation_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_self(id)),
):
    """Verificar estado de confirmación de email"""
    controller = AuthController(db)
    user = controller.get_user_profile(user_id)

    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "last_name": user.last_name,
        "email_confirmed": user.email_confirmed,
        "confirmation_sent_at": user.confirmation_sent_at,
        "role": user.role.value,
    }


# Nueva ruta para cambiar rol (solo admins)
@router.patch("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    new_role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Cambiar rol de usuario (solo admins)"""
    if new_role not in ["admin", "client", "artist"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol inválido. Roles válidos: admin, client, artist"
        )
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes cambiar tu propio rol",
        )

    controller = AuthController(db)
    user = controller.get_user_profile(user_id)
    
    # Actualizar rol
    from ..models.usuario import UserRole
    user.role = UserRole(new_role)
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"Rol actualizado a {new_role}",
        "user_id": user.id,
        "email": user.email,
        "new_role": user.role.value
    }