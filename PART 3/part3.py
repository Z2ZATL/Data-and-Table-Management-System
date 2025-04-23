from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ฟังก์ชันเชื่อมต่อฐานข้อมูล
def get_db_connection():
    conn = sqlite3.connect('mock_data.db')
    conn.row_factory = sqlite3.Row
    return conn

# หน้าแรก - ฟอร์มกรอกข้อมูลผู้ใช้
@app.route("/")
def index():
    return render_template("index.html")

# รับข้อมูลจากฟอร์มและบันทึกลง SQLite
@app.route("/submit", methods=["POST"])
def submit():
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    gender = request.form["gender"]
    age = request.form["age"]
    province = request.form["province"]

    conn = get_db_connection()
    conn.execute("INSERT INTO users (first_name, last_name, gender, age, province) VALUES (?, ?, ?, ?, ?)",
                 (first_name, last_name, gender, age, province))
    conn.commit()
    conn.close()
    return redirect("/data")

# แสดงข้อมูลทั้งหมด
@app.route("/data")
def data():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("data.html", users=users)

if __name__ == "__main__":
    app.run(debug=True)
