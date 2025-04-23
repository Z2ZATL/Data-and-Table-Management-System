from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify  # นำเข้า Flask และอื่นๆ
import sqlite3  # นำเข้า sqlite3 สำหรับเชื่อมต่อกับฐานข้อมูล
import os  # นำเข้า os เพื่อใช้งานตัวแปรสิ่งแวดล้อม
import scraping  # นำเข้าโมดูล scraping ที่สร้างไว้

app = Flask(__name__)  # สร้างแอป Flask
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")  # ตั้งค่า secret key สำหรับความปลอดภัย

# ฟังก์ชันช่วยสำหรับการจัดการธีม
def get_theme_from_cookie(request):
    theme = request.cookies.get('theme', 'dark')
    
    # ถ้าเป็น system_dark ให้ใช้ธีมมืด
    if theme == 'system_dark':
        return 'dark'
    
    # ถ้าเป็น system_light ให้ใช้ธีมสว่าง
    if theme == 'system_light':
        return 'light'
    
    # กรณีเป็นโหมดอื่นๆ ให้ใช้ค่าที่ได้รับจาก cookie โดยตรง
    return theme

def get_db_connection():  # ฟังก์ชันที่ใช้ในการเชื่อมต่อกับฐานข้อมูล
    conn = sqlite3.connect('mock_data.db')  # เชื่อมต่อกับฐานข้อมูล mock_data.db
    conn.row_factory = sqlite3.Row  # ให้ผลลัพธ์จากการดึงข้อมูลเป็น dictionary
    return conn  # ส่งกลับการเชื่อมต่อกับฐานข้อมูล

@app.route("/")  # route สำหรับหน้าแรก
def index():
    theme = get_theme_from_cookie(request)
    return render_template("index.html", theme=theme)  # ส่งไฟล์ HTML ที่ชื่อ "index.html" พร้อมข้อมูลธีม

@app.route("/about")  # route สำหรับหน้าเกี่ยวกับ
def about():
    theme = get_theme_from_cookie(request)
    return render_template("about.html", theme=theme)

@app.route("/settings")  # route สำหรับหน้าตั้งค่า
def settings():
    theme = get_theme_from_cookie(request)
    return render_template("settings.html", theme=theme)
    
@app.route("/set-theme", methods=["POST"])  # route สำหรับเปลี่ยนธีม
def set_theme():
    theme = request.form.get("theme", "dark")
    response = make_response(jsonify({"status": "success", "theme": theme}))
    response.set_cookie("theme", theme, max_age=60*60*24*365)  # ตั้งคุกกี้เก็บไว้ 1 ปี
    return response

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
        
        # นับจำนวนผู้ใช้ทั้งหมดเพื่อคำนวณหน้าสุดท้าย
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        items_per_page = 50  # จำนวนรายการต่อหน้า
        last_page = (total_users + items_per_page - 1) // items_per_page  # คำนวณหน้าสุดท้าย
        
        conn.close()  # ปิดการเชื่อมต่อกับฐานข้อมูล
        
        # เปลี่ยนเส้นทางไปที่หน้าสุดท้ายของข้อมูล
        return redirect(url_for('data', page=last_page))
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}", 500

@app.route("/data")  # route สำหรับการแสดงข้อมูล
@app.route("/data/<int:page>")  # route รองรับการเปลี่ยนหน้า
def data(page=1):
    try:
        items_per_page = 50  # จำนวนรายการต่อหน้า
        offset = (page - 1) * items_per_page  # คำนวณตำแหน่งเริ่มต้น
        
        conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
        
        # นับจำนวนผู้ใช้ทั้งหมด
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        
        # ดึงข้อมูลเฉพาะส่วนที่ต้องการแสดงในหน้านี้
        users = conn.execute(
            "SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?", 
            (items_per_page, offset)
        ).fetchall()
        
        # คำนวณจำนวนหน้าทั้งหมด
        total_pages = (total_users + items_per_page - 1) // items_per_page
        
        conn.close()  # ปิดการเชื่อมต่อกับฐานข้อมูล
        
        # คำนวณตำแหน่งเริ่มต้นของการนับลำดับ
        start_index = (page - 1) * items_per_page + 1
        
        # ดึงธีมจาก cookie
        theme = get_theme_from_cookie(request)
        
        return render_template(
            "data.html", 
            users=users, 
            total_users=total_users,
            page=page,
            total_pages=total_pages,
            start_index=start_index,
            theme=theme
        )  # ส่งข้อมูลที่ดึงมาไปแสดงใน template data.html
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
        
        # ดึงธีมจาก cookie
        theme = get_theme_from_cookie(request)
        
        return render_template("analysis.html", users=users, stats=stats, theme=theme)  # ส่งข้อมูลที่แปลงแล้วและสถิติไปแสดงใน template
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการวิเคราะห์ข้อมูล: {str(e)}", 500

@app.route("/edit/<int:user_id>", methods=["GET", "POST"])  # route สำหรับแก้ไขข้อมูล
def edit(user_id):
    try:
        conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
        
        if request.method == "POST":
            # รับข้อมูลจากฟอร์ม
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            gender = request.form["gender"]
            age = request.form["age"]
            province = request.form["province"]
            pet = request.form["pet"]
            
            # ตรวจสอบความถูกต้องของข้อมูล
            if not first_name or not last_name or not gender or not age or not province:
                return "ข้อมูลไม่ครบถ้วน กรุณากรอกข้อมูลให้ครบทุกช่อง", 400
            
            try:
                age = int(age)  # แปลงอายุเป็นตัวเลข
                if age <= 0 or age > 120:
                    return "อายุต้องอยู่ระหว่าง 1-120 ปี", 400
            except ValueError:
                return "อายุต้องเป็นตัวเลขเท่านั้น", 400
            
            # อัพเดทข้อมูลในฐานข้อมูล
            conn.execute(
                """UPDATE users SET 
                    first_name = ?, last_name = ?, gender = ?, age = ?, 
                    province = ?, pet = ? 
                   WHERE id = ?""", 
                (first_name, last_name, gender, age, province, pet, user_id)
            )
            conn.commit()
            
            # ค้นหาว่าข้อมูลผู้ใช้นี้อยู่ในหน้าไหน
            items_per_page = 50  # จำนวนรายการต่อหน้า
            user_position = conn.execute("SELECT COUNT(*) FROM users WHERE id <= ?", (user_id,)).fetchone()[0]
            user_page = (user_position + items_per_page - 1) // items_per_page
            
            conn.close()
            
            # กลับไปที่หน้าที่ข้อมูลผู้ใช้นี้อยู่
            return redirect(url_for('data', page=user_page))
        
        # ดึงข้อมูลของผู้ใช้ที่ต้องการแก้ไข
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        
        if not user:
            return "ไม่พบข้อมูลผู้ใช้", 404
        
        # ดึงธีมจาก cookie
        theme = get_theme_from_cookie(request)
        
        return render_template("edit.html", user=user, theme=theme)  # แสดงฟอร์มแก้ไขข้อมูล
    
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการแก้ไขข้อมูล: {str(e)}", 500

@app.route("/delete/<int:user_id>", methods=["GET"])  # route สำหรับลบข้อมูล
def delete(user_id):
    try:
        conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
        
        # ค้นหาว่าข้อมูลผู้ใช้นี้อยู่ในหน้าไหนก่อนลบ
        items_per_page = 50  # จำนวนรายการต่อหน้า
        user_position = conn.execute("SELECT COUNT(*) FROM users WHERE id <= ?", (user_id,)).fetchone()[0]
        current_page = (user_position + items_per_page - 1) // items_per_page
        
        # นับจำนวนผู้ใช้ทั้งหมด
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        
        # ลบข้อมูลผู้ใช้จากฐานข้อมูล
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        
        # คำนวณจำนวนหน้าทั้งหมดหลังจากลบ
        total_pages = ((total_users - 1) + items_per_page - 1) // items_per_page
        
        # ถ้าหน้าปัจจุบันมากกว่าจำนวนหน้าทั้งหมดหลังลบ ให้ไปหน้าสุดท้าย
        if current_page > total_pages and total_pages > 0:
            current_page = total_pages
        
        conn.close()
        
        # กลับไปที่หน้าเดิม หรือหน้าสุดท้ายถ้าหน้าเดิมไม่มีแล้ว
        return redirect(url_for('data', page=current_page))
    
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการลบข้อมูล: {str(e)}", 500

@app.route("/scraping")  # route สำหรับหน้าการดึงข้อมูลจากเว็บไซต์
def scraping_page():
    # ดึงธีมจาก cookie
    theme = get_theme_from_cookie(request)
    return render_template("scraping_new.html", theme=theme)

@app.route("/scrape-website", methods=["POST"])  # route สำหรับการดึงข้อมูลจากเว็บไซต์
def scrape_website():
    try:
        # รับค่า URL จากฟอร์ม
        url = request.form.get("url", "")
        
        if not url:
            return render_template("scraping_new.html", error="กรุณาระบุ URL", theme=get_theme_from_cookie(request))
        
        # ดึงข้อมูลจากเว็บไซต์
        content = scraping.get_data_from_website(url)
        
        # ส่งข้อมูลไปแสดงผล
        return render_template(
            "scraping_new.html", 
            content=content, 
            searched_url=url, 
            isinstance=isinstance, 
            dict=dict,
            list=list,
            theme=get_theme_from_cookie(request)
        )
    except Exception as e:
        return render_template(
            "scraping_new.html", 
            error=f"เกิดข้อผิดพลาด: {str(e)}", 
            theme=get_theme_from_cookie(request)
        )

if __name__ == "__main__":  # เมื่อรันไฟล์นี้โดยตรง
    app.run(debug=True)  # เริ่มต้น Flask app ในโหมด debug
