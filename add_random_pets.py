import sqlite3
import random

# รายชื่อสัตว์เลี้ยงยอดนิยมในไทย
pet_list = [
    'สุนัข', 'แมว', 'ปลาทอง', 'นก', 'กระต่าย', 'เต่า', 'แฮมสเตอร์', 'กระรอก',
    'งู', 'หนูแฮมสเตอร์', 'หนูแกสบี้', 'ปลากัด', 'ปลาหางนกยูง', 'ไก่', 'หมู', 'ชูการ์ไกลเดอร์',
    'หมูแคระ', 'ปลาคาร์ฟ', 'นกแก้ว', 'นกเขา', 'กระรอกบิน', 'อิกัวน่า', 
    'ปลาหมอสี', 'กบ', 'แพะ', 'แกะ', 'ม้า', 'วัว', 'ควาย', 'กิ้งก่า'
]

# โอกาสที่ผู้ใช้จะมีสัตว์เลี้ยง (100%) - เพิ่มทุกคนที่ยังไม่มีสัตว์เลี้ยง
pet_probability = 1.0

# เชื่อมต่อกับฐานข้อมูล
def get_db_connection():
    conn = sqlite3.connect('mock_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def add_random_pets():
    conn = get_db_connection()
    
    try:
        # ดึงข้อมูลผู้ใช้ทั้งหมด
        users = conn.execute("SELECT id, pet FROM users").fetchall()
        
        updates = 0
        for user in users:
            # ถ้าผู้ใช้ยังไม่มีสัตว์เลี้ยงหรือค่าเป็น NULL
            if user['pet'] is None or user['pet'] == '':
                # สุ่มว่าจะมีสัตว์เลี้ยงหรือไม่
                if random.random() < pet_probability:
                    # สุ่มสัตว์เลี้ยง
                    random_pet = random.choice(pet_list)
                    
                    # อัพเดตข้อมูลในฐานข้อมูล
                    conn.execute("UPDATE users SET pet = ? WHERE id = ?", (random_pet, user['id']))
                    updates += 1
        
        # ยืนยันการอัพเดต
        conn.commit()
        print(f"เพิ่มข้อมูลสัตว์เลี้ยงแบบสุ่มให้กับผู้ใช้จำนวน {updates} คน")
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_random_pets()