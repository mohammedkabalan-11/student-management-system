from pydantic import BaseModel, EmailStr
from typing import Optional

class StudentBase(BaseModel):
    student_code: str
    first_name: str
    last_name: str
    email: EmailStr
    major: str

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    student_code: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    major: Optional[str] = None

class StudentResponse(StudentBase):
    id: int
    profile_image: Optional[str] = None
    
    class Config:
        from_attributes = True