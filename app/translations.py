MESSAGES = {
    "ar": {
        "welcome": "أهلاً بك في نظام إدارة الطلاب",
        "email_exists": "البريد الإلكتروني مسجل مسبقاً",
        "student_created": "تم إنشاء الطالب بنجاح",
        "student_not_found": "الطالب غير موجود",
    },
    "en": {
        "welcome": "Welcome to Student Management System API",
        "email_exists": "Email already registered",
        "student_created": "Student created successfully",
        "student_not_found": "Student not found",
    }
}

def get_message(key: str, lang: str = "ar") -> str:
    # تحديد اللغة (الافتراضي هو العربية إذا أرسل المستخدم لغة غير مدعومة)
    selected_lang = lang.lower() if lang and lang.lower() in MESSAGES else "ar"
    return MESSAGES[selected_lang].get(key, key)