from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify  # นำเข้า Flask และอื่นๆ
import sqlite3  # นำเข้า sqlite3 สำหรับเชื่อมต่อกับฐานข้อมูล
import os  # นำเข้า os เพื่อใช้งานตัวแปรสิ่งแวดล้อม
import scraping  # นำเข้าโมดูล scraping ที่สร้างไว้
import json  # นำเข้า json สำหรับการแปลงข้อมูล
import psycopg2  # นำเข้า psycopg2 สำหรับเชื่อมต่อกับฐานข้อมูล PostgreSQL
from psycopg2.extras import RealDictCursor  # เพื่อรับผลลัพธ์เป็น dictionary

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

def get_db_connection():  # ฟังก์ชันที่ใช้ในการเชื่อมต่อกับฐานข้อมูล SQLite
    conn = sqlite3.connect('mock_data.db')  # เชื่อมต่อกับฐานข้อมูล mock_data.db
    conn.row_factory = sqlite3.Row  # ให้ผลลัพธ์จากการดึงข้อมูลเป็น dictionary
    return conn  # ส่งกลับการเชื่อมต่อกับฐานข้อมูล

def get_pg_connection():  # ฟังก์ชันที่ใช้ในการเชื่อมต่อกับฐานข้อมูล PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL)
    return conn  # ส่งกลับการเชื่อมต่อกับฐานข้อมูล

@app.route("/")  # route สำหรับหน้าแรก
def index():
    theme = get_theme_from_cookie(request)
    
    # ดึงหัวข้อทั้งหมดจากฐานข้อมูล PostgreSQL
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, title, description, created_at, updated_at
            FROM topics
            ORDER BY updated_at DESC
        """)
        topics = cur.fetchall()
        
        # ดึงเนื้อหาของแต่ละหัวข้อ
        for topic in topics:
            cur.execute("""
                SELECT id, content, content_type, created_at
                FROM topic_content
                WHERE topic_id = %s
                ORDER BY created_at DESC
            """, (topic['id'],))
            topic['contents'] = cur.fetchall()
        
        cur.close()
        conn.close()
    except Exception as e:
        topics = []
        print(f"Error fetching topics: {str(e)}")
    
    return render_template("index.html", theme=theme, topics=topics)  # ส่งไฟล์ HTML ที่ชื่อ "index.html" พร้อมข้อมูลธีมและหัวข้อ

@app.route("/topics", methods=["GET"])  # route สำหรับหน้าจัดการหัวข้อ
def topics():
    theme = get_theme_from_cookie(request)
    
    # ดึงหัวข้อทั้งหมดจากฐานข้อมูล PostgreSQL
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, title, description, created_at, updated_at
            FROM topics
            ORDER BY updated_at DESC
        """)
        topics = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        topics = []
        print(f"Error fetching topics: {str(e)}")
    
    return render_template("topics.html", theme=theme, topics=topics)

@app.route("/topics/add", methods=["GET", "POST"])  # route สำหรับเพิ่มหัวข้อใหม่
def add_topic():
    theme = get_theme_from_cookie(request)
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        
        if not title:
            return render_template("topic_form_updated.html", theme=theme, error="กรุณาระบุชื่อหัวข้อ")
        
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO topics (title, description)
                VALUES (%s, %s)
                RETURNING id
            """, (title, description))
            
            new_topic_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            return redirect(url_for('edit_topic', topic_id=new_topic_id))
        except Exception as e:
            return render_template("topic_form_updated.html", theme=theme, 
                                  error=f"เกิดข้อผิดพลาดในการบันทึกหัวข้อ: {str(e)}",
                                  title=title, description=description)
    
    return render_template("topic_form_updated.html", theme=theme)

@app.route("/topics/edit/<int:topic_id>", methods=["GET", "POST"])  # route สำหรับแก้ไขหัวข้อ
def edit_topic(topic_id):
    theme = get_theme_from_cookie(request)
    
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            
            if not title:
                return render_template("topic_form_updated.html", theme=theme, error="กรุณาระบุชื่อหัวข้อ", topic_id=topic_id)
            
            cur.execute("""
                UPDATE topics 
                SET title = %s, description = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (title, description, topic_id))
            conn.commit()
            
            return redirect(url_for('topics'))
        
        # ดึงข้อมูลหัวข้อ
        cur.execute("SELECT * FROM topics WHERE id = %s", (topic_id,))
        topic = cur.fetchone()
        
        if not topic:
            return "ไม่พบหัวข้อที่ต้องการแก้ไข", 404
        
        # ดึงเนื้อหาของหัวข้อ
        cur.execute("""
            SELECT id, content, content_type, created_at
            FROM topic_content
            WHERE topic_id = %s
            ORDER BY created_at DESC
        """, (topic_id,))
        contents = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template("topic_form_updated.html", theme=theme, topic=topic, contents=contents)
        
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการดึงข้อมูลหัวข้อ: {str(e)}", 500

@app.route("/topics/delete/<int:topic_id>", methods=["GET"])  # route สำหรับลบหัวข้อ
def delete_topic(topic_id):
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM topics WHERE id = %s", (topic_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return redirect(url_for('topics'))
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการลบหัวข้อ: {str(e)}", 500

@app.route("/topics/<int:topic_id>/content/add", methods=["POST"])  # route สำหรับเพิ่มเนื้อหาในหัวข้อ
def add_topic_content(topic_id):
    content_type = request.form.get("content_type", "text")
    is_table = request.form.get("is_table", "0") == "1"
    
    if is_table:
        # จัดการข้อมูลตาราง
        table_data = request.form.get("table_data", "{}")
        if not table_data:
            return redirect(url_for('edit_topic', topic_id=topic_id, error="ไม่มีข้อมูลตาราง"))
        
        # ใช้ข้อมูลในรูปแบบ JSON ที่ได้รับจากฟอร์ม
        content = table_data
        content_type = "table"
    else:
        # จัดการเนื้อหาทั่วไป
        content = request.form.get("content", "").strip()
        if not content:
            return redirect(url_for('edit_topic', topic_id=topic_id, error="กรุณากรอกเนื้อหา"))
    
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO topic_content (topic_id, content, content_type)
            VALUES (%s, %s, %s)
        """, (topic_id, content, content_type))
        
        # อัพเดทเวลาแก้ไขล่าสุดของหัวข้อ
        cur.execute("""
            UPDATE topics 
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (topic_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return redirect(url_for('edit_topic', topic_id=topic_id))
    except Exception as e:
        return redirect(url_for('edit_topic', topic_id=topic_id, error=f"เกิดข้อผิดพลาดในการเพิ่มเนื้อหา: {str(e)}"))

@app.route("/topics/content/delete/<int:content_id>", methods=["GET"])  # route สำหรับลบเนื้อหาในหัวข้อ
def delete_topic_content(content_id):
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        
        # ดึง topic_id ก่อนลบเนื้อหา
        cur.execute("SELECT topic_id FROM topic_content WHERE id = %s", (content_id,))
        result = cur.fetchone()
        
        if not result:
            return "ไม่พบเนื้อหาที่ต้องการลบ", 404
        
        topic_id = result[0]
        
        # ลบเนื้อหา
        cur.execute("DELETE FROM topic_content WHERE id = %s", (content_id,))
        
        # อัพเดทเวลาแก้ไขล่าสุดของหัวข้อ
        cur.execute("""
            UPDATE topics 
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (topic_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return redirect(url_for('edit_topic', topic_id=topic_id))
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการลบเนื้อหา: {str(e)}", 500

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

@app.route("/view/<int:user_id>")  # route สำหรับดูรายละเอียดผู้ใช้
def view_user(user_id):
    try:
        conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
        
        # ดึงข้อมูลของผู้ใช้
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        
        if not user:
            return "ไม่พบข้อมูลผู้ใช้", 404
        
        # ดึงธีมจาก cookie
        theme = get_theme_from_cookie(request)
        
        return render_template("view_user.html", user=user, theme=theme)  # แสดงรายละเอียดผู้ใช้
    
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการดึงข้อมูลผู้ใช้: {str(e)}", 500
        
@app.route("/edit/<int:user_id>", methods=["GET", "POST"])  # route สำหรับแก้ไขข้อมูลผู้ใช้
def edit_user(user_id):
    try:
        conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
        
        if request.method == "POST":
            # รับข้อมูลจากฟอร์ม
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            gender = request.form["gender"]
            age = request.form["age"]
            province = request.form["province"]
            pet = request.form["pet"] if request.form["pet"] else None
            
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
                "UPDATE users SET first_name = ?, last_name = ?, gender = ?, age = ?, province = ?, pet = ? WHERE id = ?",
                (first_name, last_name, gender, age, province, pet, user_id)
            )
            conn.commit()
            
            return redirect(url_for('data'))  # กลับไปหน้าข้อมูลผู้ใช้
        
        # ถ้าเป็น GET request ให้ดึงข้อมูลของผู้ใช้มาแสดงในฟอร์ม
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        
        if not user:
            return "ไม่พบข้อมูลผู้ใช้", 404
        
        # ดึงธีมจาก cookie
        theme = get_theme_from_cookie(request)
        
        return render_template("edit.html", user=user, theme=theme)  # แสดงฟอร์มแก้ไขข้อมูล
    
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการแก้ไขข้อมูลผู้ใช้: {str(e)}", 500
    
@app.route("/delete/<int:user_id>")  # route สำหรับลบข้อมูลผู้ใช้
def delete_user(user_id):
    try:
        conn = get_db_connection()  # เชื่อมต่อกับฐานข้อมูล
        
        # ตรวจสอบว่ามีผู้ใช้รหัสนี้หรือไม่
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        
        if not user:
            return "ไม่พบข้อมูลผู้ใช้", 404
        
        # ลบข้อมูลผู้ใช้จากฐานข้อมูล
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        return redirect(url_for('data'))  # กลับไปหน้าข้อมูลผู้ใช้
        
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการลบข้อมูลผู้ใช้: {str(e)}", 500
        
@app.route("/add")  # route สำหรับหน้าเพิ่มข้อมูลผู้ใช้
def add_user():
    # ดึงธีมจาก cookie
    theme = get_theme_from_cookie(request)
    return render_template("add_user.html", theme=theme)

@app.route("/scraping")  # route สำหรับหน้าการดึงข้อมูลจากเว็บไซต์
def scraping_page():
    # ดึงธีมจาก cookie
    theme = get_theme_from_cookie(request)
    return render_template("scraping_financial.html", theme=theme)

@app.route("/scrape-headlines", methods=["POST"])  # route สำหรับการดึงหัวข้อข่าวจากเว็บไซต์
def scrape_headlines():
    try:
        # รับค่า URL จากฟอร์ม
        url = request.form.get("url", "")
        
        # รับค่าตัวเลือกการกรองข่าวเกี่ยวกับข้อมูลตัวเลข
        filter_value = request.form.get("filter_numerical", "off")
        print(f"Debug - filter_value from form: {filter_value}")
        filter_numerical = filter_value == "on"
        print(f"Debug - filter_numerical after conversion: {filter_numerical}")
        
        if not url:
            return render_template("scraping_financial.html", error="กรุณาระบุ URL", theme=get_theme_from_cookie(request))
        
        # ดึงหัวข้อข่าวจากเว็บไซต์ พร้อมส่งตัวเลือกการกรอง
        headlines = scraping.get_news_headlines(url, filter_numerical)
        
        if not headlines:
            error_message = "ไม่พบหัวข้อข่าวในเว็บไซต์นี้" 
            if filter_numerical:
                error_message += " ที่เกี่ยวกับข้อมูลตัวเลข"
            error_message += " หรือเว็บไซต์ไม่รองรับการดึงหัวข้อข่าว"
            
            return render_template(
                "scraping_financial.html",
                error=error_message,
                theme=get_theme_from_cookie(request),
                filter_numerical=filter_numerical,
                searched_url=url
            )
        
        # ส่งข้อมูลไปแสดงผล
        return render_template(
            "scraping_financial.html", 
            headlines=headlines, 
            searched_url=url,
            filter_numerical=filter_numerical,
            theme=get_theme_from_cookie(request)
        )
    except Exception as e:
        return render_template(
            "scraping_financial.html", 
            error=f"เกิดข้อผิดพลาดในการดึงหัวข้อข่าว: {str(e)}", 
            filter_numerical=filter_numerical if 'filter_numerical' in locals() else False,
            searched_url=url if 'url' in locals() else "",
            theme=get_theme_from_cookie(request)
        )

@app.route("/scrape-website", methods=["POST"])  # route สำหรับการดึงข้อมูลจากเว็บไซต์
def scrape_website():
    try:
        # รับค่า URL จากฟอร์ม
        url = request.form.get("url", "")
        
        if not url:
            return render_template("scraping_financial.html", error="กรุณาระบุ URL", theme=get_theme_from_cookie(request))
        
        # รับค่าการใช้งาน AI จากฟอร์ม
        use_ai = request.form.get("use_ai", "on") == "on"
        
        # รับค่าโหมดการดึงข้อมูล (ทั่วไป หรือ ตาราง)
        extract_mode = request.form.get("extract_mode", "general")
        
        content = None
        chart_data = None
        
        # ดึงข้อมูลตามโหมดที่เลือก
        if extract_mode == "table":
            # ดึงข้อมูลตารางหุ้นหรือข้อมูลตัวเลขโดยตรง
            table_data = scraping.extract_stock_tables(url)
            
            if table_data:
                # ตรวจสอบว่ามีรูปภาพใน table_data หรือไม่
                images = table_data.pop('images', None) if isinstance(table_data, dict) else None
                
                # สร้างข้อมูลในรูปแบบที่เทมเพลตเข้าใจ
                content = {
                    'content': f"**ข้อมูลตารางจาก** {url}",
                    'ai_table': table_data
                }
                
                # ถ้ามีรูปภาพ ให้เพิ่มลงใน content
                if images:
                    content['images'] = images
            else:
                return render_template(
                    "scraping_financial.html", 
                    error="ไม่พบตารางข้อมูลในเว็บไซต์นี้ หรือรูปแบบไม่รองรับ", 
                    searched_url=url,
                    theme=get_theme_from_cookie(request)
                )
        else:
            # ดึงข้อมูลทั่วไปจากเว็บไซต์
            result = scraping.get_data_from_website(url, use_ai=use_ai)
            
            # ตรวจสอบประเภทของข้อมูลที่ได้รับ
            if isinstance(result, str):
                # กรณีที่ได้ข้อความแจ้งเตือนเป็น string
                content = result
                chart_data = None
            elif isinstance(result, dict) and 'content' in result:
                # กรณีที่ได้ข้อมูลเป็น dict ที่มีคีย์ content
                content = result
                chart_data = result.get('chart_data')
            else:
                # กรณีที่ได้ข้อมูลอื่นๆ
                content = result
                chart_data = None
        
        # ส่งข้อมูลไปแสดงผล
        return render_template(
            "scraping_financial.html", 
            content=content,
            chart_data=chart_data,
            searched_url=url, 
            isinstance=isinstance, 
            dict=dict,
            list=list,
            json=json,
            theme=get_theme_from_cookie(request)
        )
    except Exception as e:
        return render_template(
            "scraping_financial.html", 
            error=f"เกิดข้อผิดพลาด: {str(e)}", 
            theme=get_theme_from_cookie(request)
        )

# ฟังก์ชันฟิลเตอร์สำหรับแปลง JSON string เป็น Python object
@app.template_filter('fromjson')
def fromjson(value):
    try:
        return json.loads(value)
    except:
        return {}

if __name__ == "__main__":  # เมื่อรันไฟล์นี้โดยตรง
    app.run(debug=True)  # เริ่มต้น Flask app ในโหมด debug
