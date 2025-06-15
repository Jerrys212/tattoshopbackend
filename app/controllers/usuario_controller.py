from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta

from ..models.usuario import AuthUser
from ..schemas.usuario_schema import UserCreate, UserLogin, PasswordUpdate
from ..utils.security import hash_password, verify_password, create_access_token


class AuthController:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: UserCreate) -> AuthUser:
        """Crear un nuevo usuario"""

        existing_username = (
            self.db.query(AuthUser)
            .filter(AuthUser.username == user_data.username)
            .first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está registrado",
            )

        existing_email = (
            self.db.query(AuthUser).filter(AuthUser.email == user_data.email).first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado",
            )

        allowed_permissions = ["user", "admin"]

        for permission in user_data.permissions:
            if permission not in allowed_permissions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Permiso '{permission}' no válido. Permisos permitidos: {allowed_permissions}",
                )

        hashed_password = hash_password(user_data.password)

        db_user = AuthUser(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            permissions=user_data.permissions,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, login_data: UserLogin) -> tuple[AuthUser, str]:
        """Autenticar usuario y generar token"""

        user = (
            self.db.query(AuthUser).filter(AuthUser.email == login_data.email).first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario desactivado"
            )

        # Verificar contraseña
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
            )

        # Actualizar último login
        user.last_login = datetime.utcnow()
        self.db.commit()

        # Crear token JWT - ✅ CORRECCIÓN: Pasar user.id como entero
        access_token_expires = timedelta(days=30)
        access_token = create_access_token(
            data={
                "sub": user.id,  # Se convertirá a string automáticamente en create_access_token
                "username": user.username,
                "permissions": user.permissions,
            },
            expires_delta=access_token_expires,
        )

        return user, access_token

    def get_user_profile(self, user_id: int) -> AuthUser:
        """Obtener perfil de usuario"""
        user = self.db.query(AuthUser).filter(AuthUser.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )
        return user

    def update_password(self, user_id: int, password_data: PasswordUpdate) -> AuthUser:
        """Actualizar contraseña del usuario"""
        user = self.get_user_profile(user_id)

        # Verificar contraseña actual
        if not verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta",
            )

        # Actualizar con nueva contraseña
        user.password_hash = hash_password(password_data.new_password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        """Eliminar usuario"""
        user = self.get_user_profile(user_id)
        self.db.delete(user)
        self.db.commit()
        return True

    def deactivate_user(self, user_id: int) -> AuthUser:
        """Desactivar usuario (alternativa a eliminar)"""
        user = self.get_user_profile(user_id)
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_all_users(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> List[AuthUser]:
        """Obtener lista de usuarios"""
        query = self.db.query(AuthUser)

        if is_active is not None:
            query = query.filter(AuthUser.is_active == is_active)

        return query.offset(skip).limit(limit).all()
