from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify  # นำเข้า Flask และอื่นๆ
import os  # นำเข้า os เพื่อใช้งานตัวแปรสิ่งแวดล้อม
import scraping  # นำเข้าโมดูล scraping ที่สร้างไว้
import json  # นำเข้า json สำหรับการแปลงข้อมูล
import psycopg2  # นำเข้า psycopg2 สำหรับเชื่อมต่อกับฐานข้อมูล PostgreSQL
from psycopg2.extras import RealDictCursor  # เพื่อรับผลลัพธ์เป็น dictionary
import pandas as pd  # นำเข้า pandas สำหรับการจัดการข้อมูลตาราง
import tempfile  # สำหรับสร้างไฟล์ชั่วคราว
import io  # สำหรับ io operations
from werkzeug.utils import secure_filename  # สำหรับความปลอดภัยของชื่อไฟล์

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

@app.route("/upload", methods=["GET", "POST"])  # route สำหรับอัพโหลดไฟล์ข้อมูล
def upload_data():
    theme = get_theme_from_cookie(request)
    
    if request.method == "POST":
        # รับข้อมูลจากฟอร์ม
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        import_method = request.form.get("import_method", "file")
        
        if not title:
            return render_template("upload_data.html", theme=theme, error="กรุณาระบุชื่อหัวข้อ")
        
        try:
            # เริ่มสร้างหัวข้อใหม่
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO topics (title, description)
                VALUES (%s, %s)
                RETURNING id
            """, (title, description))
            
            new_topic_id = cur.fetchone()[0]
            
            # ตรวจสอบวิธีการนำเข้า
            table_data = None
            
            if import_method == "file":
                # อัพโหลดไฟล์
                if 'data_file' not in request.files:
                    return render_template("upload_data.html", theme=theme, error="ไม่พบไฟล์ที่อัพโหลด")
                
                data_file = request.files['data_file']
                
                if data_file.filename == '':
                    return render_template("upload_data.html", theme=theme, error="ไม่ได้เลือกไฟล์")
                
                # ตรวจสอบนามสกุลไฟล์
                filename = secure_filename(data_file.filename)
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext not in ['.csv', '.xlsx', '.xls', '.tsv']:
                    return render_template("upload_data.html", theme=theme, error="รูปแบบไฟล์ไม่รองรับ (รองรับเฉพาะ .csv, .xlsx, .xls และ .tsv)")
                
                # อ่านข้อมูลจากไฟล์
                try:
                    if file_ext in ['.xlsx', '.xls']:
                        df = pd.read_excel(data_file)
                    elif file_ext == '.csv':
                        df = pd.read_csv(data_file)
                    elif file_ext == '.tsv':
                        df = pd.read_csv(data_file, sep='\t')
                    
                    # แปลงข้อมูลเป็นรูปแบบที่ต้องการ
                    headers = df.columns.tolist()
                    rows = df.values.tolist()
                    
                    # แปลงเซลล์ที่เป็น NaN ให้เป็นค่าว่าง
                    rows = [['' if pd.isna(cell) else cell for cell in row] for row in rows]
                    
                    table_data = {
                        'headers': headers,
                        'rows': rows
                    }
                except Exception as e:
                    conn.rollback()
                    cur.execute("DELETE FROM topics WHERE id = %s", (new_topic_id,))
                    conn.commit()
                    return render_template("upload_data.html", theme=theme, error=f"ไม่สามารถอ่านข้อมูลจากไฟล์ได้: {str(e)}")
            
            else:  # method == "manual"
                # กรอกข้อมูลเอง
                table_data_str = request.form.get("table_data", "")
                
                if not table_data_str:
                    return render_template("upload_data.html", theme=theme, error="ไม่มีข้อมูลตาราง")
                
                try:
                    table_data = json.loads(table_data_str)
                except:
                    return render_template("upload_data.html", theme=theme, error="ข้อมูลตารางไม่ถูกต้อง")
            
            # เพิ่มเนื้อหาตารางในหัวข้อ
            if table_data:
                # ตรวจสอบความถูกต้องของข้อมูล
                if 'headers' not in table_data or 'rows' not in table_data:
                    return render_template("upload_data.html", theme=theme, error="รูปแบบข้อมูลตารางไม่ถูกต้อง")
                
                # แปลงข้อมูลเป็น JSON string
                content = json.dumps(table_data)
                
                # บันทึกลงฐานข้อมูล
                cur.execute("""
                    INSERT INTO topic_content (topic_id, content, content_type)
                    VALUES (%s, %s, %s)
                """, (new_topic_id, content, "table"))
                
                conn.commit()
                cur.close()
                conn.close()
                
                return render_template("upload_data.html", theme=theme, success=f"สร้างหัวข้อและข้อมูลตารางสำเร็จแล้ว")
            else:
                conn.rollback()
                cur.execute("DELETE FROM topics WHERE id = %s", (new_topic_id,))
                conn.commit()
                return render_template("upload_data.html", theme=theme, error="ไม่มีข้อมูลตารางที่จะบันทึก")
            
        except Exception as e:
            return render_template("upload_data.html", theme=theme, error=f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}")
    
    return render_template("upload_data.html", theme=theme)

@app.route("/data")  # route สำหรับข้อมูลตาราง
def data():
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
        
        # ดึงเนื้อหาของแต่ละหัวข้อที่เป็นตาราง
        for topic in topics:
            cur.execute("""
                SELECT id, content, content_type, created_at
                FROM topic_content
                WHERE topic_id = %s AND content_type = 'table'
                ORDER BY created_at DESC
            """, (topic['id'],))
            topic['table_contents'] = cur.fetchall()
        
        cur.close()
        conn.close()
    except Exception as e:
        topics = []
        print(f"Error fetching topics data: {str(e)}")
    
    return render_template("data.html", theme=theme, topics=topics)

@app.route("/data/edit-table/<int:content_id>", methods=["GET", "POST"])  # route สำหรับแก้ไขข้อมูลตาราง
def edit_table_data(content_id):
    theme = get_theme_from_cookie(request)
    
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # ดึงข้อมูลเนื้อหาตาราง
        cur.execute("""
            SELECT tc.id, tc.content, tc.content_type, tc.created_at, tc.topic_id, 
                   t.title, t.description, t.created_at as topic_created_at, t.updated_at as topic_updated_at
            FROM topic_content tc
            JOIN topics t ON tc.topic_id = t.id
            WHERE tc.id = %s AND tc.content_type = 'table'
        """, (content_id,))
        
        result = cur.fetchone()
        
        if not result:
            return "ไม่พบข้อมูลตารางที่ต้องการแก้ไข", 404
        
        topic = {
            'id': result['topic_id'],
            'title': result['title'],
            'description': result['description'],
            'created_at': result['topic_created_at'],
            'updated_at': result['topic_updated_at']
        }
        
        # หากเป็นการส่งฟอร์ม POST เพื่อบันทึกการแก้ไข
        if request.method == "POST":
            table_data_str = request.form.get("table_data", "")
            
            if not table_data_str:
                return render_template("edit_table_data.html", 
                                      theme=theme, 
                                      error="ไม่มีข้อมูลตาราง", 
                                      topic=topic,
                                      content_id=content_id,
                                      table_data=json.loads(result['content']))
            
            try:
                table_data = json.loads(table_data_str)
                
                # ตรวจสอบความถูกต้องของข้อมูล
                if 'headers' not in table_data or 'rows' not in table_data:
                    return render_template("edit_table_data.html", 
                                          theme=theme, 
                                          error="รูปแบบข้อมูลตารางไม่ถูกต้อง", 
                                          topic=topic,
                                          content_id=content_id,
                                          table_data=json.loads(result['content']))
                
                # แปลงข้อมูลเป็น JSON string
                content = json.dumps(table_data)
                
                # บันทึกการเปลี่ยนแปลง
                cur.execute("""
                    UPDATE topic_content 
                    SET content = %s
                    WHERE id = %s
                """, (content, content_id))
                
                # อัพเดทเวลาแก้ไขล่าสุดของหัวข้อ
                cur.execute("""
                    UPDATE topics 
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (result['topic_id'],))
                
                conn.commit()
                
                return redirect(url_for('data'))
                
            except Exception as e:
                return render_template("edit_table_data.html", 
                                      theme=theme, 
                                      error=f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}", 
                                      topic=topic,
                                      content_id=content_id,
                                      table_data=json.loads(result['content']))
        
        # แสดงฟอร์มแก้ไข (GET)
        table_data = json.loads(result['content'])
        
        cur.close()
        conn.close()
        
        return render_template("edit_table_data.html", 
                              theme=theme, 
                              topic=topic,
                              content_id=content_id,
                              table_data=table_data)
        
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการดึงข้อมูลตาราง: {str(e)}", 500

@app.route("/data/add-table", methods=["GET", "POST"])  # route สำหรับเพิ่มข้อมูลตาราง
def add_table_data():
    theme = get_theme_from_cookie(request)
    
    if request.method == "POST":
        # รับข้อมูลจากฟอร์ม
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        table_data_str = request.form.get("table_data", "")
        
        if not title:
            return render_template("edit_table_data.html", 
                                  theme=theme, 
                                  error="กรุณาระบุชื่อหัวข้อ")
        
        if not table_data_str:
            return render_template("edit_table_data.html", 
                                  theme=theme, 
                                  error="ไม่มีข้อมูลตาราง",
                                  title=title,
                                  description=description)
        
        try:
            # แปลงข้อมูลตารางจาก JSON string
            table_data = json.loads(table_data_str)
            
            # ตรวจสอบความถูกต้องของข้อมูล
            if 'headers' not in table_data or 'rows' not in table_data:
                return render_template("edit_table_data.html", 
                                      theme=theme, 
                                      error="รูปแบบข้อมูลตารางไม่ถูกต้อง",
                                      title=title,
                                      description=description)
            
            # เริ่มต้นบันทึกข้อมูล
            conn = get_pg_connection()
            cur = conn.cursor()
            
            # สร้างหัวข้อใหม่
            cur.execute("""
                INSERT INTO topics (title, description)
                VALUES (%s, %s)
                RETURNING id
            """, (title, description))
            
            new_topic_id = cur.fetchone()[0]
            
            # บันทึกข้อมูลตาราง
            content = json.dumps(table_data)
            
            cur.execute("""
                INSERT INTO topic_content (topic_id, content, content_type)
                VALUES (%s, %s, %s)
            """, (new_topic_id, content, "table"))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return redirect(url_for('data'))
            
        except Exception as e:
            return render_template("edit_table_data.html", 
                                  theme=theme, 
                                  error=f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}",
                                  title=title,
                                  description=description)
    
    # สร้างตารางเปล่า
    empty_table = {
        "headers": ["คอลัมน์ 1", "คอลัมน์ 2"],
        "rows": [[""]]
    }
    
    # สร้างหัวข้อเปล่า
    topic = {
        'id': None,
        'title': '',
        'description': '',
        'created_at': None,
        'updated_at': None
    }
    
    return render_template("edit_table_data.html", 
                          theme=theme, 
                          topic=topic,
                          content_id=None,
                          table_data=empty_table,
                          is_new=True)



@app.route("/analysis")  # route สำหรับหน้าการวิเคราะห์ข้อมูล
def analysis():
    try:
        # ดึงธีมจาก cookie
        theme = get_theme_from_cookie(request)
        
        # ดึงหัวข้อที่มีข้อมูลตารางจากฐานข้อมูล PostgreSQL
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # ดึงหัวข้อที่มีเนื้อหาประเภทตาราง
        cur.execute("""
            SELECT t.id, t.title, t.description 
            FROM topics t
            JOIN topic_content tc ON t.id = tc.topic_id
            WHERE tc.content_type = 'table'
            GROUP BY t.id, t.title, t.description
            ORDER BY t.updated_at DESC
        """)
        topics_with_tables = cur.fetchall()
        
        # สำหรับแต่ละหัวข้อ ดึงเนื้อหาประเภทตารางล่าสุด
        for topic in topics_with_tables:
            cur.execute("""
                SELECT id, content, created_at
                FROM topic_content
                WHERE topic_id = %s AND content_type = 'table'
                ORDER BY created_at DESC
                LIMIT 1
            """, (topic['id'],))
            latest_table = cur.fetchone()
            
            if latest_table:
                # แปลงข้อมูล JSON เป็น dictionary
                try:
                    table_data = json.loads(latest_table['content'])
                    topic['table_data'] = table_data
                except Exception as e:
                    print(f"Error parsing table data: {str(e)}")
                    topic['table_data'] = None
        
        cur.close()
        conn.close()
        
        return render_template("analysis.html", topics=topics_with_tables, theme=theme)
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการวิเคราะห์ข้อมูล: {str(e)}", 500



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

# ฟังก์ชันฟิลเตอร์สำหรับแปลง Python object เป็น JSON string
@app.template_filter('tojson')
def tojson_filter(obj):
    return json.dumps(obj)

if __name__ == "__main__":  # เมื่อรันไฟล์นี้โดยตรง
    app.run(debug=True)  # เริ่มต้น Flask app ในโหมด debug
