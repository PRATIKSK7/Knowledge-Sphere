from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.STUDENT
    institution: Optional[str] = None
    bio: Optional[str] = None
    research_interests: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    institution: Optional[str] = None
    bio: Optional[str] = None
    research_interests: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
