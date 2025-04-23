from flask import Flask, render_template, request, redirect  # นำเข้า Flask, render_template, request, redirect
import sqlite3  # นำเข้า sqlite3 สำหรับเชื่อมต่อกับฐานข้อมูล

app = Flask(__name__)  # สร้างแอป Flask

def get_db_connection():  # ฟังก์ชันที่ใช้ในการเชื่อมต่อกับฐานข้อมูล
    conn = sqlite3.connect('mock_data.db')  # เชื่อมต่อกับฐานข้อมูล mock_data.db
    conn.row_factory = sqlite3.Row  # ให้ผลลัพธ์จากการดึงข้อมูลเป็น dictionary
    return conn  # ส่งกลับการเชื่อมต่อกับฐานข้อมูล

@app.route("/")  # route สำหรับหน้าแรก
def index():
    return render_template("index.html")  # ส่งไฟล์ HTML ที่ชื่อ "index.html" กลับไปที่ผู้ใช้

@app.route("/submit", methods=["POST"])  # route สำหรับรับข้อมูลจากฟอร์ม
def submit():
    first_name = request.form["first_name"]  # รับค่าชื่อจากฟอร์ม
    last_name = request.form["last_name"]  # รับค่านามสกุลจากฟอร์ม
    gender = request.form["gender"]  # รับค่าเพศจากฟอร์ม
    age = request.form["age"]  # รับค่าอายุจากฟอร์ม
    province = request.form["province"]  # รับค่าจังหวัดจากฟอร์ม

    conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
    conn.execute("INSERT INTO users (first_name, last_name, gender, age, province) VALUES (?, ?, ?, ?, ?)",
                 (first_name, last_name, gender, age, province))  # บันทึกข้อมูลลงในฐานข้อมูล
    conn.commit()  # ยืนยันการบันทึกข้อมูล
    conn.close()  # ปิดการเชื่อมต่อกับฐานข้อมูล
    return redirect("/data")  # เปลี่ยนเส้นทางไปที่หน้า /data เพื่อแสดงข้อมูล

@app.route("/data")  # route สำหรับการแสดงข้อมูล
def data():
    conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
    users = conn.execute("SELECT * FROM users").fetchall()  # ดึงข้อมูลทั้งหมดจากตาราง users
    conn.close()  # ปิดการเชื่อมต่อกับฐานข้อมูล
    return render_template("data.html", users=users)  # ส่งข้อมูลที่ดึงมาไปแสดงใน template data.html

@app.route("/analysis")  # route สำหรับหน้าการวิเคราะห์ข้อมูล
def analysis():
    conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
    rows = conn.execute("SELECT * FROM users").fetchall()  # ดึงข้อมูลทั้งหมดจากตาราง users
    conn.close()  # ปิดการเชื่อมต่อกับฐานข้อมูล

    users = [dict(row) for row in rows]  # แปลงข้อมูลจาก Row เป็น dictionary เพื่อใช้งานใน HTML
    return render_template("analysis.html", users=users)  # ส่งข้อมูลที่แปลงแล้วไปแสดงใน template analysis.html

if __name__ == "__main__":  # เมื่อรันไฟล์นี้โดยตรง
    app.run(debug=True)  # เริ่มต้น Flask app ในโหมด debug
