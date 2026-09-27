from sqlalchemy import Column, Integer, String
from .database import Base

class StudentModel(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    major = Column(String, nullable=False)
    profile_image = Column(String, nullable=True)  # مسار الصورة الشخصية