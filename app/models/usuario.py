# models/usuario.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from .database import Base  # ← Importante: importar Base desde database.py
from datetime import datetime
import bcrypt
import enum

# ← NO definas Base aquí de nuevo, usa la importada

class UserRole(enum.Enum):
    ADMIN = "admin"
    CLIENT = "client" 
    ARTIST = "artist"

class User(Base):  # ← Usar la Base importada
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    email_confirmed = Column(Boolean, default=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CLIENT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Agregar campos para confirmación de email
    confirmation_token = Column(String(10), nullable=True)
    confirmation_sent_at = Column(DateTime, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    def set_password(self, password: str):
        salt = bcrypt.gensalt(rounds=12)
        self.password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"