import os
import shutil
import io
import csv
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import sqlite3

# إعداد قاعدة البيانات (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./students.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# إنشاء مجلد لحفظ الصور المرفوعة إذا لم يكن موجوداً
UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 1. نموذج قاعدة البيانات (SQLAlchemy Model)
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    major = Column(String)
    gender = Column(String, default="ذكر")  # حقل الجنس
    profile_image = Column(String, nullable=True)  # مسار الصورة

Base.metadata.create_all(bind=engine)

# التحقق التلقائي وإضافة عمود الجنس إن لم يكن موجوداً في قاعدة بيانات سابقة
try:
    conn = sqlite3.connect('students.db')
    conn.execute("ALTER TABLE students ADD COLUMN gender TEXT DEFAULT 'ذكر';")
    conn.commit()
    conn.close()
except sqlite3.OperationalError:
    pass

app = FastAPI(title="نظام إدارة الطلاب الشامل")

# ربط المجلدات الثابتة لخدمة عرض الصور والملفات
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# دالة الاعتمادية لجلسة قاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. مسار عرض واجهة المستخدم (Frontend UI)
@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
async def serve_ui():
    file_path = "app/templates/index.html"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>عذراً، لم يتم العثور على ملف واجهة المستخدم (index.html) في المسار app/templates/</h3>"

# 3. مسار جلب وعرض جميع الطلاب (مع دعم البحث)
@app.get("/students/")
def get_students(search: str = None, db: Session = Depends(get_db)):
    query = db.query(Student)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Student.first_name.ilike(search_term)) |
            (Student.last_name.ilike(search_term)) |
            (Student.student_code.ilike(search_term)) |
            (Student.major.ilike(search_term)) |
            (Student.email.ilike(search_term))
        )
    students = query.all()
    result = []
    for s in students:
        result.append({
            "id": s.id,
            "student_code": s.student_code,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "email": s.email,
            "major": s.major,
            "gender": s.gender or "ذكر",
            "profile_image": f"/{s.profile_image}" if s.profile_image else None
        })
    return result

# 4. مسار تصدير بيانات الطلاب إلى ملف Excel (CSV) - [تم التعديل لإصلاح مشكلة ترميز الأحرف العربية]
@app.get("/students/export/csv")
def export_students_csv(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'كود الطالب', 'الاسم الأول', 'اسم العائلة', 'البريد الإلكتروني', 'التخصص', 'الجنس'])
    for s in students:
        writer.writerow([
            s.id, 
            s.student_code, 
            s.first_name, 
            s.last_name, 
            s.email, 
            s.major, 
            s.gender or "ذكر"
        ])
    output.seek(0)
    
    # إضافة علامة الترتيب البايتي (BOM) لكي يتعرف Excel تلقائياً على ترميز الحروف العربية
    csv_content = "\ufeff" + output.getvalue()
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students_report.csv"}
    )

# 5. مسار إضافة طالب جديد
@app.post("/students/")
async def create_student(
    student_code: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    major: str = Form(...),
    gender: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    existing_student = db.query(Student).filter(Student.student_code == student_code).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="كود الطالب مستخدم مسبقاً، يجب أن يكون فريداً.")

    image_path = None
    if file:
        file_extension = file.filename.split(".")[-1]
        file_name = f"{student_code}_{os.urandom(4).hex()}.{file_extension}"
        full_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        image_path = f"app/static/uploads/{file_name}"

    new_student = Student(
        student_code=student_code,
        first_name=first_name,
        last_name=last_name,
        email=email,
        major=major,
        gender=gender,
        profile_image=image_path
    )
    
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {"message": "تم إضافة الطالب بنجاح", "id": new_student.id}

# 6. مسار تعديل بيانات طالب
@app.put("/students/{student_id}")
async def update_student(
    student_id: int,
    student_code: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    major: str = Form(...),
    gender: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    student.student_code = student_code
    student.first_name = first_name
    student.last_name = last_name
    student.email = email
    student.major = major
    student.gender = gender

    if file:
        if student.profile_image and os.path.exists(student.profile_image):
            os.remove(student.profile_image)
            
        file_extension = file.filename.split(".")[-1]
        file_name = f"{student_code}_{os.urandom(4).hex()}.{file_extension}"
        full_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        student.profile_image = f"app/static/uploads/{file_name}"

    db.commit()
    return {"message": "تم تحديث بيانات الطالب بنجاح"}

# 7. مسار حذف طالب
@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    if student.profile_image and os.path.exists(student.profile_image):
        os.remove(student.profile_image)

    db.delete(student)
    db.commit()
    return {"message": "تم حذف الطالب بنجاح"}   