from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# Schema para crear usuario
class UserCreate(BaseModel):
    username: str = Field(
        min_length=3, max_length=50, description="Nombre de usuario único"
    )
    email: EmailStr = Field(description="Email del usuario")
    password: str = Field(
        min_length=6, max_length=100, description="Contraseña (mínimo 6 caracteres)"
    )
    permissions: List[str] = Field(default=["user"], description="Lista de permisos")


# Schema para login
class UserLogin(BaseModel):
    email: EmailStr = Field(description="Email para iniciar sesión")
    password: str = Field(description="Contraseña")


# Schema para actualizar contraseña
class PasswordUpdate(BaseModel):
    current_password: str = Field(description="Contraseña actual")
    new_password: str = Field(
        min_length=6, max_length=100, description="Nueva contraseña"
    )


# Schema para respuesta de usuario (sin contraseña)
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    permissions: List[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Schema para respuesta de login (con token)
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int = 3600  # segundos


# Schema para token payload
class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    permissions: Optional[List[str]] = None


# Schema para lista de usuarios
class UserListItem(BaseModel):
    id: int
    username: str
    email: str
    permissions: List[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Schema para lista paginada
class UserList(BaseModel):
    users: List[UserListItem]
    total: int
    page: int
    per_page: int
