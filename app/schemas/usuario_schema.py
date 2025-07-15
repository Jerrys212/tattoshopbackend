from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime

# Schema para crear usuario
class UserCreate(BaseModel):
    name: str = Field(
        min_length=1, max_length=50, description="Nombre del usuario"
    )
    last_name: str = Field(
        min_length=1, max_length=50, description="Apellido del usuario"
    )
    email: EmailStr = Field(description="Email del usuario")
    password: str = Field(
        min_length=6, max_length=100, description="Contraseña (mínimo 6 caracteres)"
    )
    role: Optional[Literal["admin", "client", "artist"]] = Field(
        default="client", description="Rol del usuario"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        return v.strip()
    
    @field_validator('last_name')
    @classmethod
    def validate_last_name(cls, v):
        return v.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return v.lower().strip()

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

# Schema para confirmación de email
class EmailConfirmation(BaseModel):
    token: str = Field(description="Token de confirmación")

# Schema para reenviar confirmación
class ResendConfirmation(BaseModel):
    email: EmailStr = Field(description="Email para reenviar confirmación")

# Schema para actualizar usuario
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[Literal["admin", "client", "artist"]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            return v.strip()
        return v
    
    @field_validator('last_name')
    @classmethod
    def validate_last_name(cls, v):
        if v is not None:
            return v.strip()
        return v

# Schema para respuesta de usuario (sin contraseña)
class UserResponse(BaseModel):
    id: int
    name: str
    last_name: str
    email: str
    role: str
    email_confirmed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

# Schema para respuesta de login (con token)
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int = 3600

# Schema para token payload
class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

# Schema para lista de usuarios
class UserListItem(BaseModel):
    id: int
    name: str
    last_name: str
    email: str
    role: str
    email_confirmed: bool
    created_at: datetime

    model_config = {"from_attributes": True}

# Schema para lista paginada
class UserList(BaseModel):
    users: List[UserListItem]
    total: int
    page: int
    per_page: int

# Schema para respuesta de registro
class RegisterResponse(BaseModel):
    message: str
    user: UserResponse
    confirmation_required: bool = True