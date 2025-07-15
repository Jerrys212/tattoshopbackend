from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import string

from ..models.usuario import User, UserRole
from ..schemas.usuario_schema import (
    UserCreate,
    UserLogin,
    PasswordUpdate,
    EmailConfirmation,
    ResendConfirmation,
)
from ..utils.security import (
    create_access_token,
)
from ..services.email_service import EmailService


class AuthController:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()

    def generate_confirmation_token(self, length: int = 6) -> str:
        """Generar token alfanumérico de confirmación"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))

    def create_user(self, user_data: UserCreate) -> User:
        """Crear un nuevo usuario y enviar email de confirmación"""

        # Verificar si el email ya existe
        existing_email = (
            self.db.query(User).filter(User.email == user_data.email).first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado",
            )

        # Crear nuevo usuario sin confirmar
        db_user = User(
            name=user_data.name,
            last_name=user_data.last_name,
            email=user_data.email,
            role=UserRole(user_data.role),
            email_confirmed=False,  # Usuario sin confirmar por defecto
        )

        # Hashear contraseña usando el método del modelo
        db_user.set_password(user_data.password)

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        # Enviar email de confirmación
        try:
            self.send_confirmation_email(db_user)
        except Exception as e:
            print(f"Error enviando email de confirmación: {e}")
            # No fallar el registro si el email falla
            pass

        return db_user

    def send_confirmation_email(self, user: User) -> bool:
        """Enviar email de confirmación"""
        # Generar token de confirmación alfanumérico
        confirmation_token = self.generate_confirmation_token(6)  # Token de 6 dígitos

        # Guardar token en la base de datos (necesitarás agregar estos campos al modelo)
        user.confirmation_token = confirmation_token
        user.confirmation_sent_at = datetime.utcnow()
        user.token_expires_at = datetime.utcnow() + timedelta(hours=24)  # Expira en 24 horas
        self.db.commit()

        # Enviar email
        return self.email_service.send_confirmation_email(
            user.email, f"{user.name} {user.last_name}", confirmation_token
        )

    def confirm_email(self, confirmation_data: EmailConfirmation) -> User:
        """Confirmar email del usuario"""
        
        user = (
            self.db.query(User)
            .filter(User.confirmation_token == confirmation_data.token)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de confirmación inválido",
            )

        if user.email_confirmed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta ya está confirmada",
            )

        # Verificar si el token ha expirado
        if user.token_expires_at and datetime.utcnow() > user.token_expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El token de confirmación ha expirado",
            )

        # Confirmar usuario
        user.email_confirmed = True
        user.confirmation_token = None
        user.token_expires_at = None
        user.confirmation_sent_at = None
        self.db.commit()
        self.db.refresh(user)

        # Enviar email de bienvenida
        try:
            self.email_service.send_welcome_email(
                user.email, f"{user.name} {user.last_name}"
            )
        except Exception as e:
            print(f"Error enviando email de bienvenida: {e}")

        return user

    def resend_confirmation_email(self, resend_data: ResendConfirmation) -> bool:
        """Reenviar email de confirmación"""
        user = (
            self.db.query(User).filter(User.email == resend_data.email).first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Usuario no encontrado"
            )

        if user.email_confirmed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta ya está confirmada",
            )

        # Verificar límite de tiempo entre envíos
        if user.confirmation_sent_at:
            time_since_last = datetime.utcnow() - user.confirmation_sent_at
            if time_since_last < timedelta(minutes=2):  # 2 minutos de espera
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Debes esperar al menos 2 minutos antes de solicitar otro email",
                )

        return self.send_confirmation_email(user)

    def authenticate_user(self, login_data: UserLogin) -> tuple[User, str]:
        """Autenticar usuario y generar token"""

        user = (
            self.db.query(User).filter(User.email == login_data.email).first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
            )

        if not user.email_confirmed:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Debes confirmar tu email antes de iniciar sesión. Revisa tu bandeja de entrada.",
            )

        # Usar el método del modelo para verificar contraseña
        if not user.check_password(login_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
            )

        # Actualizar timestamp de último login (necesitarás agregar este campo)
        # user.last_login = datetime.utcnow()
        self.db.commit()

        # Crear token JWT
        access_token_expires = timedelta(days=30)
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "role": user.role.value,
            },
            expires_delta=access_token_expires,
        )

        return user, access_token

    def get_user_profile(self, user_id: int) -> User:
        """Obtener perfil de usuario"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Usuario no encontrado"
            )
        return user

    def update_password(self, user_id: int, password_data: PasswordUpdate) -> User:
        """Actualizar contraseña del usuario"""
        user = self.get_user_profile(user_id)

        # Verificar contraseña actual usando el método del modelo
        if not user.check_password(password_data.current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta",
            )

        # Actualizar con nueva contraseña
        user.set_password(password_data.new_password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        """Eliminar usuario"""
        user = self.get_user_profile(user_id)
        self.db.delete(user)
        self.db.commit()
        return True

    def get_all_users(
        self, skip: int = 0, limit: int = 100, role: Optional[str] = None
    ) -> List[User]:
        """Obtener lista de usuarios"""
        query = self.db.query(User)

        if role:
            try:
                user_role = UserRole(role)
                query = query.filter(User.role == user_role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rol '{role}' no válido"
                )

        return query.offset(skip).limit(limit).all()