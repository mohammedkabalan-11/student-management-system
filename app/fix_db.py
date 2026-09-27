import sqlite3

def fix_database():
    try:
        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE students ADD COLUMN gender TEXT DEFAULT 'ذكر';")
        conn.commit()
        conn.close()
        print("تمت إضافة حقل الجنس إلى قاعدة البيانات بنجاح!")
    except Exception as e:
        print("ملاحظة: يبدو أن الحقل موجود مسبقاً أو أن القاعدة فارغة:", e)

if __name__ == "__main__":
    fix_database()