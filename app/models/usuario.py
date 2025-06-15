from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from .database import Base


class AuthUser(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)  # Contraseña hasheada

    permissions = Column(JSON, nullable=False, default=["user"])
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<AuthUser(id={self.id}, username='{self.username}', email='{self.email}')>"

    def to_dict(self):
        """Convertir modelo a diccionario (sin contraseña)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "permissions": self.permissions,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
        }

    def has_permission(self, permission: str) -> bool:
        """Verificar si el usuario tiene un permiso específico"""
        return permission in self.permissions or "admin" in self.permissions
