import os
import json
import requests
import re

# ดึง API key จากตัวแปรสภาพแวดล้อม
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# ดึง Gemini API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"

# กำหนด API ที่จะใช้งาน (DEEPSEEK หรือ GEMINI)
API_PROVIDER = "GEMINI" if GEMINI_API_KEY else "DEEPSEEK"

# ตั้งค่า AI model
MODEL_NAME = "deepseek-chat"  # สำหรับ Deepseek
GEMINI_MODEL = "gemini-1.5-pro"  # สำหรับ Gemini

def is_about_numerical_data(headline_text):
    """
    ใช้ AI วิเคราะห์ว่าหัวข้อข่าวเกี่ยวกับข้อมูลตัวเลขหรือไม่
    
    Args:
        headline_text (str): หัวข้อข่าวที่ต้องการวิเคราะห์
        
    Returns:
        bool: True หากเกี่ยวกับข้อมูลตัวเลข, False หากไม่เกี่ยวข้อง
    """
    # ตรวจสอบว่าจะใช้ API ไหน
    if API_PROVIDER == "GEMINI" and GEMINI_API_KEY:
        return is_about_numerical_data_gemini(headline_text)
    elif API_PROVIDER == "DEEPSEEK" and DEEPSEEK_API_KEY:
        return is_about_numerical_data_deepseek(headline_text)
    else:
        print("Warning: No valid API KEY found for AI providers")
        return None


def is_about_numerical_data_gemini(headline_text):
    """
    ใช้ Gemini AI วิเคราะห์ว่าหัวข้อข่าวเกี่ยวกับข้อมูลตัวเลขหรือไม่
    
    Args:
        headline_text (str): หัวข้อข่าวที่ต้องการวิเคราะห์
        
    Returns:
        bool: True หากเกี่ยวกับข้อมูลตัวเลข, False หากไม่เกี่ยวข้อง
    """
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not found in environment variables")
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
        
        # ส่งคำขอไปยัง Gemini API
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 10,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        # เพิ่ม API key เข้าไปใน URL
        gemini_url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        response = requests.post(
            gemini_url,
            headers=headers,
            data=json.dumps(data),
            timeout=10
        )
        
        # ตรวจสอบว่า API ตอบกลับสำเร็จหรือไม่
        if response.status_code == 200:
            result = response.json()
            answer = result["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
            
            # ตรวจสอบคำตอบ
            return "yes" in answer
        else:
            print(f"Error from Gemini API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception when calling Gemini API: {str(e)}")
        return None


def is_about_numerical_data_deepseek(headline_text):
    """
    ใช้ Deepseek AI วิเคราะห์ว่าหัวข้อข่าวเกี่ยวกับข้อมูลตัวเลขหรือไม่
    
    Args:
        headline_text (str): หัวข้อข่าวที่ต้องการวิเคราะห์
        
    Returns:
        bool: True หากเกี่ยวกับข้อมูลตัวเลข, False หากไม่เกี่ยวข้อง
    """
    if not DEEPSEEK_API_KEY:
        print("Warning: DEEPSEEK_API_KEY not found in environment variables")
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

def summarize_article_with_ai(text):
    """
    สรุปเนื้อหาบทความโดยใช้ AI
    
    Args:
        text (str): เนื้อหาบทความที่ต้องการสรุป
        
    Returns:
        str: เนื้อหาบทความที่ถูกสรุปแล้ว หรือ None ถ้าไม่สามารถสรุปได้
    """
    # ตรวจสอบว่าจะใช้ API ไหน
    if API_PROVIDER == "GEMINI" and GEMINI_API_KEY:
        return summarize_article_with_gemini(text)
    elif API_PROVIDER == "DEEPSEEK" and DEEPSEEK_API_KEY:
        return summarize_article_with_deepseek(text)
    else:
        print("Warning: No valid API KEY found for AI providers")
        return None


def summarize_article_with_gemini(text):
    """
    สรุปเนื้อหาบทความโดยใช้ Gemini AI
    
    Args:
        text (str): เนื้อหาบทความที่ต้องการสรุป
        
    Returns:
        str: เนื้อหาบทความที่ถูกสรุปแล้ว หรือ None ถ้าไม่สามารถสรุปได้
    """
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not found in environment variables")
        return None
    
    if not text or len(text) < 100:
        return text
    
    try:
        # คำนวณความยาวของเนื้อหา และจำกัดเนื้อหาที่ส่งไป AI
        prompt_limit = 8000
        if len(text) > prompt_limit:
            text = text[:prompt_limit] + "..."
            
        # สร้าง prompt สำหรับสรุปบทความ
        prompt = f"""
        สรุปเนื้อหาต่อไปนี้ให้กระชับและเข้าใจง่าย โดยเน้นสาระสำคัญ ข้อมูลตัวเลข สถิติ และข้อเท็จจริงที่สำคัญ
        สรุปเป็นภาษาไทยที่อ่านง่าย ความยาวไม่เกิน 300 คำ:
        
        {text}
        """
        
        # ส่งคำขอไปยัง Gemini API
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1000,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        # เพิ่ม API key เข้าไปใน URL
        gemini_url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        response = requests.post(
            gemini_url,
            headers=headers,
            data=json.dumps(data),
            timeout=20
        )
        
        # ตรวจสอบว่า API ตอบกลับสำเร็จหรือไม่
        if response.status_code == 200:
            result = response.json()
            summary = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # เพิ่มหัวข้อสรุป
            summary = "## 🤖 สรุปโดย AI (Gemini)\n\n" + summary
            
            return summary
        else:
            print(f"Error from Gemini API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception when calling Gemini API for summarization: {str(e)}")
        return None


def summarize_article_with_deepseek(text):
    """
    สรุปเนื้อหาบทความโดยใช้ Deepseek AI
    
    Args:
        text (str): เนื้อหาบทความที่ต้องการสรุป
        
    Returns:
        str: เนื้อหาบทความที่ถูกสรุปแล้ว หรือ None ถ้าไม่สามารถสรุปได้
    """
    if not DEEPSEEK_API_KEY:
        print("Warning: DEEPSEEK_API_KEY not found in environment variables")
        return None
    
    if not text or len(text) < 100:
        return text
    
    try:
        # คำนวณความยาวของเนื้อหา และจำกัดเนื้อหาที่ส่งไป AI
        prompt_limit = 8000
        if len(text) > prompt_limit:
            text = text[:prompt_limit] + "..."
            
        # สร้าง prompt สำหรับสรุปบทความ
        prompt = f"""
        สรุปเนื้อหาต่อไปนี้ให้กระชับและเข้าใจง่าย โดยเน้นสาระสำคัญ ข้อมูลตัวเลข สถิติ และข้อเท็จจริงที่สำคัญ
        สรุปเป็นภาษาไทยที่อ่านง่าย ความยาวไม่เกิน 300 คำ:
        
        {text}
        """
        
        # ส่งคำขอไปยัง Deepseek API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=20
        )
        
        # ตรวจสอบว่า API ตอบกลับสำเร็จหรือไม่
        if response.status_code == 200:
            result = response.json()
            summary = result["choices"][0]["message"]["content"].strip()
            
            # เพิ่มหัวข้อสรุป
            summary = "## 🤖 สรุปโดย AI (Deepseek)\n\n" + summary
            
            return summary
        else:
            print(f"Error from Deepseek API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception when calling Deepseek API for summarization: {str(e)}")
        return None

def extract_numerical_table_with_ai(text):
    """
    ใช้ AI สกัดข้อมูลตัวเลขจากเนื้อหาและสร้างตารางข้อมูล
    
    Args:
        text (str): เนื้อหาที่ต้องการสกัดข้อมูลตัวเลข
        
    Returns:
        dict: ข้อมูลตารางที่สกัดได้ หรือ None ถ้าไม่สามารถสกัดได้
    """
    # ตรวจสอบว่าจะใช้ API ไหน
    if API_PROVIDER == "GEMINI" and GEMINI_API_KEY:
        return extract_numerical_table_with_gemini(text)
    elif API_PROVIDER == "DEEPSEEK" and DEEPSEEK_API_KEY:
        return extract_numerical_table_with_deepseek(text)
    else:
        print("Warning: No valid API KEY found for AI providers")
        return None


def extract_numerical_table_with_gemini(text):
    """
    ใช้ Gemini AI สกัดข้อมูลตัวเลขจากเนื้อหาและสร้างตารางข้อมูล
    
    Args:
        text (str): เนื้อหาที่ต้องการสกัดข้อมูลตัวเลข
        
    Returns:
        dict: ข้อมูลตารางที่สกัดได้ หรือ None ถ้าไม่สามารถสกัดได้
    """
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not found in environment variables")
        return None
    
    if not text or len(text) < 100:
        return None
    
    try:
        # คำนวณความยาวของเนื้อหา และจำกัดเนื้อหาที่ส่งไป AI
        prompt_limit = 8000
        if len(text) > prompt_limit:
            text = text[:prompt_limit] + "..."
            
        # สร้าง prompt สำหรับสกัดข้อมูลตัวเลข
        prompt = f"""
        สกัดข้อมูลตัวเลขที่สำคัญจากเนื้อหาต่อไปนี้ และสร้างเป็นตารางข้อมูลในรูปแบบ JSON
        โดยมีฟิลด์ดังนี้:
        1. headers: รายการหัวข้อของตาราง เช่น ["ข้อมูล", "ตัวเลข", "หน่วย"]
        2. rows: รายการข้อมูลแต่ละแถว เช่น [["รายได้ปี 2567", "150", "ล้านบาท"], ["อัตราเติบโต", "12.5", "%"]]
        
        กรุณาสกัดข้อมูลเฉพาะตัวเลขที่สำคัญเท่านั้น เช่น ราคา อัตรา เปอร์เซ็นต์ สถิติ จำนวน โดยไม่ต้องรวมเรื่องเล่าหรือรายละเอียดอื่น
        ถ้าไม่พบข้อมูลตัวเลขที่สำคัญเพียงพอ ให้ตอบ "no_data"
        
        ตอบเฉพาะในรูปแบบ JSON เท่านั้น เช่น:
        {{"headers": ["ข้อมูล", "ตัวเลข", "หน่วย"], "rows": [["รายได้ปี 2567", "150", "ล้านบาท"], ["อัตราเติบโต", "12.5", "%"]]}}
        
        เนื้อหา:
        {text}
        """
        
        # ส่งคำขอไปยัง Gemini API
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2000,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        # เพิ่ม API key เข้าไปใน URL
        gemini_url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        response = requests.post(
            gemini_url,
            headers=headers,
            data=json.dumps(data),
            timeout=20
        )
        
        # ตรวจสอบว่า API ตอบกลับสำเร็จหรือไม่
        if response.status_code == 200:
            result = response.json()
            answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # ตรวจสอบว่าไม่พบข้อมูลหรือไม่
            if "no_data" in answer.lower():
                return None
                
            # พยายามแปลงข้อความเป็น JSON
            try:
                # ค้นหาส่วนที่เป็น JSON ด้วย regex
                json_match = re.search(r'({[\s\S]*})|(\[[\s\S]*\])', answer)
                if json_match:
                    json_str = json_match.group(0)
                    # แปลง JSON string เป็น Python dict
                    table_data = json.loads(json_str)
                    return table_data
                else:
                    print("Could not find JSON data in Gemini AI response")
                    return None
            except Exception as json_err:
                print(f"Error parsing JSON from Gemini AI response: {str(json_err)}")
                print(f"AI response: {answer}")
                return None
        else:
            print(f"Error from Gemini API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception when calling Gemini API for table extraction: {str(e)}")
        return None


def extract_numerical_table_with_deepseek(text):
    """
    ใช้ Deepseek AI สกัดข้อมูลตัวเลขจากเนื้อหาและสร้างตารางข้อมูล
    
    Args:
        text (str): เนื้อหาที่ต้องการสกัดข้อมูลตัวเลข
        
    Returns:
        dict: ข้อมูลตารางที่สกัดได้ หรือ None ถ้าไม่สามารถสกัดได้
    """
    if not DEEPSEEK_API_KEY:
        print("Warning: DEEPSEEK_API_KEY not found in environment variables")
        return None
    
    if not text or len(text) < 100:
        return None
    
    try:
        # คำนวณความยาวของเนื้อหา และจำกัดเนื้อหาที่ส่งไป AI
        prompt_limit = 8000
        if len(text) > prompt_limit:
            text = text[:prompt_limit] + "..."
            
        # สร้าง prompt สำหรับสกัดข้อมูลตัวเลข
        prompt = f"""
        สกัดข้อมูลตัวเลขที่สำคัญจากเนื้อหาต่อไปนี้ และสร้างเป็นตารางข้อมูลในรูปแบบ JSON
        โดยมีฟิลด์ดังนี้:
        1. headers: รายการหัวข้อของตาราง เช่น ["ข้อมูล", "ตัวเลข", "หน่วย"]
        2. rows: รายการข้อมูลแต่ละแถว เช่น [["รายได้ปี 2567", "150", "ล้านบาท"], ["อัตราเติบโต", "12.5", "%"]]
        
        กรุณาสกัดข้อมูลเฉพาะตัวเลขที่สำคัญเท่านั้น เช่น ราคา อัตรา เปอร์เซ็นต์ สถิติ จำนวน โดยไม่ต้องรวมเรื่องเล่าหรือรายละเอียดอื่น
        ถ้าไม่พบข้อมูลตัวเลขที่สำคัญเพียงพอ ให้ตอบ "no_data"
        
        เนื้อหา:
        {text}
        """
        
        # ส่งคำขอไปยัง Deepseek API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 2000
        }
        
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=20
        )
        
        # ตรวจสอบว่า API ตอบกลับสำเร็จหรือไม่
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"].strip()
            
            # ตรวจสอบว่าไม่พบข้อมูลหรือไม่
            if "no_data" in answer.lower():
                return None
                
            # พยายามแปลงข้อความเป็น JSON
            try:
                # ค้นหาส่วนที่เป็น JSON ด้วย regex
                json_match = re.search(r'({[\s\S]*})|(\[[\s\S]*\])', answer)
                if json_match:
                    json_str = json_match.group(0)
                    # แปลง JSON string เป็น Python dict
                    table_data = json.loads(json_str)
                    return table_data
                else:
                    print("Could not find JSON data in Deepseek AI response")
                    return None
            except Exception as json_err:
                print(f"Error parsing JSON from Deepseek AI response: {str(json_err)}")
                print(f"AI response: {answer}")
                return None
        else:
            print(f"Error from Deepseek API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception when calling Deepseek API for table extraction: {str(e)}")
        return None