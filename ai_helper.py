import os
import json
import requests

# ดึง API key จากตัวแปรสภาพแวดล้อม
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def is_about_numerical_data(headline_text):
    """
    ใช้ Deepseek AI วิเคราะห์ว่าหัวข้อข่าวเกี่ยวกับข้อมูลตัวเลขหรือไม่
    
    Args:
        headline_text (str): หัวข้อข่าวที่ต้องการวิเคราะห์
        
    Returns:
        bool: True หากเกี่ยวกับข้อมูลตัวเลข, False หากไม่เกี่ยวข้อง
    """
    if not DEEPSEEK_API_KEY:
        print("Warning: DEEPSEEK_API_KEY not found in environment variables")
        # ในกรณีที่ไม่มี API key ให้ใช้วิธีการเดิมในการกรอง
        return None
    
    try:
        # สร้าง prompt สำหรับวิเคราะห์หัวข้อข่าว
        prompt = f"""
        วิเคราะห์หัวข้อข่าวนี้ว่าเกี่ยวข้องกับข้อมูลตัวเลขหรือไม่: "{headline_text}"
        
        หัวข้อข่าวจะถือว่าเกี่ยวข้องกับข้อมูลตัวเลขหากมีลักษณะต่อไปนี้:
        1. มีการพูดถึงตัวเลขที่สำคัญ เช่น ราคา, อัตราการเปลี่ยนแปลง, เปอร์เซ็นต์, จำนวน, สถิติ
        2. เกี่ยวข้องกับข้อมูลทางเศรษฐกิจ เช่น ราคาหุ้น, อัตราแลกเปลี่ยน, อัตราเงินเฟ้อ, ดัชนีเศรษฐกิจ
        3. เกี่ยวข้องกับการเงิน เช่น ราคาสินค้า, ราคาน้ำมัน, ราคาทอง, งบประมาณ, รายได้, กำไร
        4. มีการพูดถึงสถิติ หรือข้อมูลเชิงปริมาณที่สำคัญ
        
        ตอบเพียง "yes" หากเกี่ยวข้อง หรือ "no" หากไม่เกี่ยวข้องเท่านั้น
        """
        
        # ส่งคำขอไปยัง Deepseek API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # ใช้ค่าต่ำเพื่อให้คำตอบคงที่
            "max_tokens": 10     # จำกัดความยาวของคำตอบ
        }
        
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=10
        )
        
        # ตรวจสอบว่า API ตอบกลับสำเร็จหรือไม่
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"].strip().lower()
            
            # ตรวจสอบคำตอบ
            return answer == "yes"
        else:
            print(f"Error from Deepseek API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception when calling Deepseek API: {str(e)}")
        return None

def filter_headlines_with_ai(headlines):
    """
    กรองหัวข้อข่าวที่เกี่ยวกับข้อมูลตัวเลขโดยใช้ AI
    
    Args:
        headlines (list): รายการหัวข้อข่าว
        
    Returns:
        list: รายการหัวข้อข่าวที่เกี่ยวกับข้อมูลตัวเลข
    """
    if not headlines:
        return []
        
    filtered_headlines = []
    
    for headline in headlines:
        title = headline.get('title', '')
        if title:
            result = is_about_numerical_data(title)
            
            # ถ้า AI วิเคราะห์ได้ว่าเกี่ยวข้องกับข้อมูลตัวเลข หรือ API ไม่ทำงานก็ใช้วิธีเดิม
            if result is True:
                filtered_headlines.append(headline)
                
    return filtered_headlines