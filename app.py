from flask import Flask, render_template, request, redirect, url_for  # นำเข้า Flask, render_template, request, redirect, url_for
import sqlite3  # นำเข้า sqlite3 สำหรับเชื่อมต่อกับฐานข้อมูล
import os  # นำเข้า os เพื่อใช้งานตัวแปรสิ่งแวดล้อม

app = Flask(__name__)  # สร้างแอป Flask
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")  # ตั้งค่า secret key สำหรับความปลอดภัย

def get_db_connection():  # ฟังก์ชันที่ใช้ในการเชื่อมต่อกับฐานข้อมูล
    conn = sqlite3.connect('mock_data.db')  # เชื่อมต่อกับฐานข้อมูล mock_data.db
    conn.row_factory = sqlite3.Row  # ให้ผลลัพธ์จากการดึงข้อมูลเป็น dictionary
    return conn  # ส่งกลับการเชื่อมต่อกับฐานข้อมูล

@app.route("/")  # route สำหรับหน้าแรก
def index():
    return render_template("index.html")  # ส่งไฟล์ HTML ที่ชื่อ "index.html" กลับไปที่ผู้ใช้

@app.route("/about")  # route สำหรับหน้าเกี่ยวกับ
def about():
    return render_template("about.html")

@app.route("/submit", methods=["POST"])  # route สำหรับรับข้อมูลจากฟอร์ม
def submit():
    try:
        first_name = request.form["first_name"]  # รับค่าชื่อจากฟอร์ม
        last_name = request.form["last_name"]  # รับค่านามสกุลจากฟอร์ม
        gender = request.form["gender"]  # รับค่าเพศจากฟอร์ม
        age = request.form["age"]  # รับค่าอายุจากฟอร์ม
        province = request.form["province"]  # รับค่าจังหวัดจากฟอร์ม
        pet = request.form["pet"]  # รับค่าสัตว์เลี้ยงจากฟอร์ม

        # ตรวจสอบความถูกต้องของข้อมูล
        if not first_name or not last_name or not gender or not age or not province:
            return "ข้อมูลไม่ครบถ้วน กรุณากรอกข้อมูลให้ครบทุกช่อง", 400
        
        try:
            age = int(age)  # แปลงอายุเป็นตัวเลข
            if age <= 0 or age > 120:
                return "อายุต้องอยู่ระหว่าง 1-120 ปี", 400
        except ValueError:
            return "อายุต้องเป็นตัวเลขเท่านั้น", 400

        conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
        conn.execute("INSERT INTO users (first_name, last_name, gender, age, province, pet) VALUES (?, ?, ?, ?, ?, ?)",
                    (first_name, last_name, gender, age, province, pet))  # บันทึกข้อมูลลงในฐานข้อมูล พร้อมสัตว์เลี้ยง
        conn.commit()  # ยืนยันการบันทึกข้อมูล
        conn.close()  # ปิดการเชื่อมต่อกับฐานข้อมูล
        return redirect(url_for('data'))  # เปลี่ยนเส้นทางไปที่หน้า /data เพื่อแสดงข้อมูล
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}", 500

@app.route("/data")  # route สำหรับการแสดงข้อมูล
def data():
    try:
        conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
        users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()  # ดึงข้อมูลทั้งหมดจากตาราง users เรียงตาม id จากน้อยไปมาก
        total_users = len(users)  # นับจำนวนผู้ใช้ทั้งหมด
        conn.close()  # ปิดการเชื่อมต่อกับฐานข้อมูล
        return render_template("data.html", users=users, total_users=total_users)  # ส่งข้อมูลที่ดึงมาไปแสดงใน template data.html
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}", 500

@app.route("/analysis")  # route สำหรับหน้าการวิเคราะห์ข้อมูล
def analysis():
    try:
        conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
        
        # ดึงข้อมูลทั้งหมดจากตาราง users
        rows = conn.execute("SELECT * FROM users").fetchall()  
        
        # ดึงข้อมูลสถิติเพิ่มเติม
        male_count = conn.execute("SELECT COUNT(*) FROM users WHERE gender = 'ชาย'").fetchone()[0]
        female_count = conn.execute("SELECT COUNT(*) FROM users WHERE gender = 'หญิง'").fetchone()[0]
        
        age_stats = conn.execute("""
            SELECT 
                AVG(age) as avg_age,
                MIN(age) as min_age,
                MAX(age) as max_age
            FROM users
        """).fetchone()
        
        # จัดกลุ่มตามจังหวัด
        province_counts = conn.execute("""
            SELECT province, COUNT(*) as count 
            FROM users 
            GROUP BY province 
            ORDER BY count DESC
            LIMIT 5
        """).fetchall()
        
        conn.close()  # ปิดการเชื่อมต่อกับฐานข้อมูล

        users = [dict(row) for row in rows]  # แปลงข้อมูลจาก Row เป็น dictionary เพื่อใช้งานใน HTML
        
        # สร้างข้อมูลสถิติเพิ่มเติม
        stats = {
            'total': len(users),
            'male': male_count,
            'female': female_count,
            'avg_age': round(age_stats[0], 1) if age_stats[0] else 0,
            'min_age': age_stats[1],
            'max_age': age_stats[2],
            'top_provinces': [{
                'name': p['province'], 
                'count': p['count']
            } for p in province_counts]
        }
        
        return render_template("analysis.html", users=users, stats=stats)  # ส่งข้อมูลที่แปลงแล้วและสถิติไปแสดงใน template
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการวิเคราะห์ข้อมูล: {str(e)}", 500

if __name__ == "__main__":  # เมื่อรันไฟล์นี้โดยตรง
    app.run(debug=True)  # เริ่มต้น Flask app ในโหมด debug
