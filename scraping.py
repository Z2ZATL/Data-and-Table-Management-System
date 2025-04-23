import trafilatura
import requests
import re
from bs4 import BeautifulSoup
import json
import ai_helper

def get_website_text_content(url):
    """
    ฟังก์ชันนี้ใช้สำหรับดึงเนื้อหาหลักจากเว็บไซต์
    
    Args:
        url (str): URL ของเว็บไซต์ที่ต้องการดึงข้อมูล
        
    Returns:
        str: เนื้อหาหลักของเว็บไซต์ที่ถูกดึงมา หรือ None ถ้าไม่สามารถดึงได้
    """
    try:
        # ส่งคำขอไปยังเว็บไซต์
        downloaded = trafilatura.fetch_url(url)
        
        # ดึงเนื้อหาหลักจาก HTML
        text = trafilatura.extract(downloaded)
        
        return text
    except Exception as e:
        print(f"Error extracting content from {url}: {str(e)}")
        return None

def format_special_content(text):
    """
    จัดรูปแบบเนื้อหาพิเศษ เช่น ผลรางวัลล็อตเตอรี่ ราคาทอง เป็นต้น
    
    Args:
        text (str): ข้อความที่ต้องการจัดรูปแบบ
        
    Returns:
        str: ข้อความที่จัดรูปแบบแล้ว
    """
    # ตรวจสอบว่าเป็นเนื้อหาเกี่ยวกับล็อตเตอรี่หรือไม่
    if "รางวัลที่ 1" in text and "เลขท้าย" in text:
        # จัดรูปแบบผลรางวัลล็อตเตอรี่
        for keyword in ["รางวัลที่ 1", "เลขท้าย 2 ตัว", "เลขหน้า 3 ตัว", "เลขท้าย 3 ตัว", "รางวัลข้างเคียง"]:
            text = text.replace(keyword, "\n\n" + keyword + "\n")
        
        # จัดรูปแบบตัวเลขให้มีช่องว่าง
        import re
        text = re.sub(r'(\d{6})(\d{6})', r'\1 \2', text)  # แยกเลขรางวัลข้างเคียง 12 หลัก
        
    # ตรวจสอบว่าเป็นเนื้อหาเกี่ยวกับราคาทองหรือไม่
    if "ราคาทองคำ" in text and "บาทละ" in text:
        # จัดรูปแบบข้อมูลราคาทอง
        for keyword in ["ราคาทองคำ", "ราคาทองคำแท่ง", "ซื้อบาทละ", "ขายบาทละ", "ราคาทองรูปพรรณ"]:
            text = text.replace(keyword, "\n\n" + keyword + "\n")
        
        # แก้ไขคำผิด
        text = text.replace("ราคาทองsูปพรรณ", "\n\nราคาทองรูปพรรณ\n")
        
        # อัปเดตเวลา
        if "อัปเดตล่าสุด" in text:
            text = text.replace("อัปเดตล่าสุด", "\n\nอัปเดตล่าสุด")
    
    return text.strip()

def get_news_headlines(url, filter_numerical=False):
    """
    ฟังก์ชันนี้ใช้สำหรับดึงหัวข้อข่าวจากเว็บไซต์
    
    Args:
        url (str): URL ของเว็บไซต์ที่ต้องการดึงหัวข้อข่าว
        filter_numerical (bool): หากเป็น True จะกรองเฉพาะข่าวที่เกี่ยวกับข้อมูลตัวเลข
        
    Returns:
        list: รายการหัวข้อข่าวพร้อมลิงก์
    """
    print(f"Debug - filter_numerical: {filter_numerical}, type: {type(filter_numerical)}")
    try:
        # ส่งคำขอไปยังเว็บไซต์
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # ตรวจสอบสถานะการตอบกลับ
        if response.status_code != 200:
            return []
        
        # ใช้ BeautifulSoup เพื่อแยกวิเคราะห์ HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ลิสต์เก็บหัวข้อข่าว
        headlines = []
        
        # คำสำคัญสำหรับกรองหัวข้อข่าวที่เกี่ยวกับข้อมูลตัวเลข
        numerical_keywords = [
            # คำเกี่ยวกับราคา
            'ราคา', 'บาท', 'ดอลลาร์', 'เงินบาท', 'หุ้น', 'ค่าเงิน', 'ดัชนี', 'ตลาดหุ้น', 'น้ำมัน', 'ทอง', 'ทองคำ',
            # คำเกี่ยวกับอัตรา
            'อัตรา', 'เปอร์เซ็นต์', 'ร้อยละ', 'เพิ่มขึ้น', 'ลดลง', '%', 'เท่า', 'ครั้ง',
            # คำเกี่ยวกับจำนวน
            'จำนวน', 'ล้าน', 'พันล้าน', 'หมื่นล้าน', 'แสนล้าน', 'ตัน', 'กิโลกรัม',
            # คำเกี่ยวกับยอดขาย
            'ยอดขาย', 'รายได้', 'กำไร', 'ขาดทุน', 'เทียบกับ', 'ไตรมาส', 'ประจำปี',
            # คำเกี่ยวกับสถิติ
            'สถิติ', 'ทำสถิติ', 'ทะลุ', 'สูงสุด', 'ต่ำสุด', 'เฉลี่ย', 'คาดการณ์', 'GDP', 'ผลิตภัณฑ์มวลรวม',
            # หน่วยงานที่เกี่ยวข้องกับเศรษฐกิจ
            'ธนาคาร', 'ธปท', 'ตลาดหลักทรัพย์', 'กระทรวงพาณิชย์', 'กระทรวงการคลัง', 'IMF', 'World Bank',
            # ข่าวตัวเลขอื่นๆ
            'อุณหภูมิ', 'ค่า PM', 'ฝุ่น', 'มลพิษ', 'จีดีพี', 'ศก.', 'เศรษฐกิจ'
        ]
        
        # หาลิงก์ที่มีโอกาสเป็นข่าว
        # 1. หาจากแท็ก <a> ที่มีข้อความยาวพอสมควร
        for a_tag in soup.find_all('a', href=True):
            # ตรวจสอบว่า href เป็น URL ที่สมบูรณ์หรือไม่
            href = a_tag['href']
            if not href.startswith(('http://', 'https://')):
                # ถ้าเป็น relative URL ให้แปลงเป็น absolute URL
                if href.startswith('/'):
                    base_url = re.match(r'(https?://[^/]+)', url).group(1)
                    href = base_url + href
                else:
                    continue  # ข้ามลิงก์ที่ไม่ใช่ URL
            
            # ตรวจสอบข้อความในลิงก์
            text = a_tag.get_text().strip()
            
            # กรองเฉพาะลิงก์ที่น่าจะเป็นข่าว (ความยาวของข้อความมากกว่า 30 ตัวอักษร)
            if len(text) > 30 and not re.search(r'\.(jpg|jpeg|png|gif|css|js)$', href, re.I):
                # ถ้าต้องการกรองเฉพาะข่าวที่เกี่ยวกับข้อมูลตัวเลข
                if filter_numerical:
                    # ตรวจสอบว่ามีคำสำคัญที่เกี่ยวกับข้อมูลตัวเลขหรือไม่
                    has_numerical_keyword = any(keyword.lower() in text.lower() for keyword in numerical_keywords)
                    
                    # มีตัวเลขในหัวข้อหรือไม่ (ต้องมีตัวเลขอย่างน้อย 1 ตัว)
                    has_number = bool(re.search(r'\d+', text))
                    
                    # เพิ่มเงื่อนไขความเข้มงวด - ต้องมีทั้งคำสำคัญและตัวเลข
                    if not (has_numerical_keyword and has_number):
                        continue
                    
                    # เพิ่มการตรวจสอบเพิ่มเติมว่ามีคำสำคัญทางเศรษฐกิจหรือสถิติหรือไม่
                    economic_keywords = ['เศรษฐกิจ', 'ราคา', 'บาท', 'ดอลลาร์', 'หุ้น', 'ธนาคาร', 'ตลาด',
                                        'ร้อยละ', '%', 'เปอร์เซ็นต์', 'ยอดขาย', 'กำไร', 'รายได้', 'ขาดทุน', 
                                        'เพิ่มขึ้น', 'ลดลง', 'สูงสุด', 'ต่ำสุด', 'อัตรา', 'สถิติ', 'จำนวน',
                                        'ล้าน', 'พันล้าน', 'หมื่นล้าน']
                    has_economic_keyword = any(keyword.lower() in text.lower() for keyword in economic_keywords)
                    
                    # ตรวจสอบว่ามีรูปแบบตัวเลขพิเศษหรือไม่ เช่น เปอร์เซ็นต์ สกุลเงิน
                    has_special_number = bool(re.search(r'(\d+(?:\.\d+)?)\s*(?:%|บาท|ดอลลาร์|ล้าน|พันล้าน|เปอร์เซ็นต์|เท่า)', text))
                    
                    # ถ้าไม่มีคำสำคัญทางเศรษฐกิจ หรือไม่มีรูปแบบตัวเลขพิเศษ ยังคัดกรองเพิ่มเติม
                    if not (has_economic_keyword or has_special_number):
                        continue
                
                # ตรวจสอบว่าลิงก์นี้อยู่ในโดเมนเดียวกันกับเว็บไซต์หลักหรือไม่
                original_domain = re.match(r'https?://([^/]+)', url).group(1)
                link_domain = re.match(r'https?://([^/]+)', href)
                
                if link_domain and (link_domain.group(1) == original_domain or 
                                   link_domain.group(1).endswith('.' + original_domain)):
                    # เพิ่มหัวข้อข่าวลงในลิสต์
                    headline = {
                        'title': text,
                        'url': href
                    }
                    
                    # ตรวจสอบความซ้ำซ้อน
                    if headline not in headlines:
                        headlines.append(headline)
        
        # ถ้าต้องการใช้ AI ในการกรองข่าวที่เกี่ยวกับข้อมูลตัวเลข
        if filter_numerical and headlines:
            print(f"Before AI filtering: {len(headlines)} headlines")
            # ใช้ AI กรองหัวข้อข่าวที่เกี่ยวกับข้อมูลตัวเลข
            ai_filtered_headlines = ai_helper.filter_headlines_with_ai(headlines)
            
            # ถ้า AI สามารถกรองได้ จะใช้ผลลัพธ์จาก AI
            if ai_filtered_headlines:
                headlines = ai_filtered_headlines
                print(f"After AI filtering: {len(headlines)} headlines")
        
        # จำกัดจำนวนหัวข้อข่าว
        return headlines[:20]  # คืนค่าแค่ 20 หัวข้อแรก
        
    except Exception as e:
        print(f"Error getting news headlines: {str(e)}")
        return []

def get_data_from_website(url, use_ai=True):
    """
    ฟังก์ชันนี้ใช้สำหรับดึงข้อมูลจากเว็บไซต์และจัดรูปแบบให้เป็นคำอธิบายสั้นๆ
    
    Args:
        url (str): URL ของเว็บไซต์ที่ต้องการดึงข้อมูล
        use_ai (bool): หากเป็น True จะใช้ AI ในการสรุปเนื้อหาและสร้างตาราง
        
    Returns:
        str: คำอธิบายสั้นๆ เกี่ยวกับเนื้อหาของเว็บไซต์
    """
    try:
        # ส่งคำขอไปยังเว็บไซต์
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # ตรวจสอบสถานะการตอบกลับ
        if response.status_code != 200:
            return f"ไม่สามารถเข้าถึงเว็บไซต์ได้ (สถานะ: {response.status_code})"
            
        # ถ้าเป็น JSON ให้ส่งคืนข้อมูล JSON
        if 'application/json' in response.headers.get('Content-Type', ''):
            return response.json()
        
        # ถ้าไม่ใช่ JSON ให้ใช้ trafilatura ดึงเนื้อหา
        downloaded = response.text
        text = trafilatura.extract(downloaded)
        
        if not text:
            return "ไม่สามารถดึงเนื้อหาจากเว็บไซต์นี้ได้"
        
        # ปรับแต่งเนื้อหา
        # แทนที่ช่องว่างซ้ำด้วยช่องว่างเดียว
        text = ' '.join(text.split())
        
        # ตรวจสอบว่าเป็นเนื้อหาพิเศษหรือไม่
        if "รางวัลที่ 1" in text or "ราคาทองคำ" in text:
            text = format_special_content(text)
        else:
            # แทนที่บรรทัดว่างซ้ำด้วยบรรทัดว่างเดียว
            text = text.replace('\n\n\n', '\n\n')
            
            # เพิ่มบรรทัดว่างหลังจุด เพื่อให้อ่านง่ายขึ้น
            text = text.replace('. ', '.\n\n')
            
            # แทนที่เครื่องหมายอื่นๆ เพื่อให้อ่านง่ายขึ้น
            text = text.replace('! ', '!\n\n')
            text = text.replace('? ', '?\n\n')
        
        # จำกัดความยาวของเนื้อหา
        if len(text) > 2000:
            # ตัดที่ประโยคที่สมบูรณ์เพื่อให้อ่านง่ายขึ้น
            cutoff = text[:1997].rfind('.')
            if cutoff > 1000:  # ถ้าพบจุดในช่วงที่เหมาะสม
                text = text[:cutoff+1] + "..."
            else:
                text = text[:1997] + "..."
        
        # สรุปเนื้อหาด้วย AI ถ้า use_ai เป็น True
        ai_summary = None
        ai_table = None
        
        if use_ai:
            # สรุปเนื้อหาด้วย AI
            ai_summary = ai_helper.summarize_article_with_ai(text)
            
            # สร้างตารางข้อมูลด้วย AI
            ai_table = ai_helper.extract_numerical_table_with_ai(text)
        
        # วิเคราะห์หาข้อมูลตัวเลขในเนื้อหาด้วยวิธีปกติ
        numerical_data = extract_numerical_data(text)
        
        # สร้างการตอบกลับที่มีทั้งเนื้อหาและข้อมูลกราฟ
        result = {
            'content': text,
            'chart_data': numerical_data,
            'ai_summary': ai_summary,
            'ai_table': ai_table
        }
            
        return result
        
    except requests.exceptions.Timeout:
        return "การเชื่อมต่อกับเว็บไซต์หมดเวลา"
    except requests.exceptions.ConnectionError:
        return "ไม่สามารถเชื่อมต่อกับเว็บไซต์"
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}"

def extract_numerical_data(text):
    """
    ฟังก์ชันสำหรับสกัดข้อมูลตัวเลขจากเนื้อหา
    
    Args:
        text (str): เนื้อหาที่ต้องการวิเคราะห์
        
    Returns:
        dict: ข้อมูลสำหรับนำไปแสดงเป็นกราฟ หรือ None ถ้าไม่พบข้อมูลตัวเลข
    """
    if not text:
        return None
        
    # แบ่งเนื้อหาเป็นประโยค
    sentences = re.split(r'[.!?]\s', text)
    
    # เก็บข้อมูลตัวเลขและบริบท
    numerical_data = []
    
    # กำหนดคำสำคัญที่มักจะเกี่ยวข้องกับตัวเลข
    important_keywords = ['เพิ่มขึ้น', 'ลดลง', 'ร้อยละ', 'เปอร์เซ็นต์', 'จำนวน', 'มูลค่า', 'บาท',
                          'ปี', 'เดือน', 'วัน', 'คน', 'ล้าน', 'พัน', 'สิบ', 'พันล้าน', 'แสน',
                          'สถิติ', 'อัตรา', 'ระดับ', 'คะแนน', 'คิดเป็น', 'ราคา', 'ดอลลาร์', 'ดัชนี']
    
    for sentence in sentences:
        # ค้นหาตัวเลขในประโยค
        # 1. ค้นหาตัวเลขทั่วไป (เช่น 12, 3.45, 67,890)
        numbers = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)', sentence)
        
        # 2. ค้นหาเปอร์เซ็นต์ (เช่น 10%, 3.5%)
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*(?:เปอร์เซ็นต์|%|ร้อยละ)', sentence)
        
        # ถ้าพบตัวเลขในประโยคนี้
        if numbers or percentages:
            # เช็คว่ามีคำสำคัญในประโยคหรือไม่
            has_keyword = any(keyword in sentence for keyword in important_keywords)
            
            # นับคำสำคัญที่พบในประโยค
            keyword_count = sum(1 for keyword in important_keywords if keyword in sentence)
            
            # เพิ่มคะแนนความสำคัญถ้ามีคำสำคัญหลายคำในประโยคเดียวกัน
            importance = keyword_count if has_keyword else 0
            
            # เพิ่มคะแนนถ้าพบเปอร์เซ็นต์
            if percentages:
                importance += 1
                
            # เก็บข้อมูลประโยคที่มีความสำคัญ
            if importance > 0:
                data = {
                    'sentence': sentence.strip(),
                    'numbers': numbers,
                    'percentages': percentages,
                    'importance': importance
                }
                numerical_data.append(data)
    
    # ถ้าไม่พบข้อมูลตัวเลขสำคัญ
    if not numerical_data:
        return None
    
    # เรียงข้อมูลตามความสำคัญ
    numerical_data.sort(key=lambda x: x['importance'], reverse=True)
    
    # เลือกข้อมูลสำคัญสูงสุด 5 รายการ
    top_data = numerical_data[:5]
    
    # เตรียมข้อมูลสำหรับแสดงผลเป็นกราฟ
    chart_data = {
        'type': 'bar',  # ค่าเริ่มต้นเป็นกราฟแท่ง
        'title': 'ข้อมูลตัวเลขจากบทความ',
        'data': []
    }
    
    # ตรวจสอบจำนวนข้อมูลที่เก็บมาได้ แล้วกำหนดชนิดของกราฟตามความเหมาะสม
    num_items = len(top_data)
    
    # กำหนดชนิดกราฟตามจำนวนข้อมูล
    if num_items <= 2:
        chart_data['type'] = 'pie'  # ใช้กราฟวงกลมถ้ามีข้อมูลน้อย
    elif any('เพิ่มขึ้น' in item['sentence'] or 'ลดลง' in item['sentence'] or 'เปลี่ยนแปลง' in item['sentence'] for item in top_data):
        chart_data['type'] = 'line'  # ใช้กราฟเส้นถ้าเกี่ยวข้องกับการเปลี่ยนแปลง
    
    # แปลงข้อมูลให้เหมาะสมกับการแสดงผลเป็นกราฟ
    labels = []
    values = []
    
    for item in top_data:
        # ใช้ประโยคที่สั้นลงเป็นป้ายชื่อ
        label = item['sentence']
        if len(label) > 50:
            label = label[:47] + '...'
        
        # ดึงตัวเลขที่สำคัญที่สุดในประโยค (เลือกตัวเลขแรก)
        value = 0
        if item['percentages']:
            value = float(item['percentages'][0])
        elif item['numbers']:
            # ลบเครื่องหมายคอมม่าและแปลงเป็นตัวเลข
            value_str = item['numbers'][0].replace(',', '')
            try:
                value = float(value_str)
            except ValueError:
                continue
        
        # เพิ่มข้อมูลลงในกราฟ
        labels.append(label)
        values.append(value)
    
    # เก็บข้อมูลสำหรับกราฟ
    chart_data['data'] = {
        'labels': labels,
        'values': values,
        'sentences': [item['sentence'] for item in top_data]
    }
    
    return chart_data

# ฟังก์ชันสำหรับดึงข้อมูลข่าวจาก RSS Feed
def get_news_from_rss(rss_url, limit=5):
    """
    ฟังก์ชันนี้ใช้สำหรับดึงข้อมูลข่าวจาก RSS Feed
    
    Args:
        rss_url (str): URL ของ RSS Feed
        limit (int): จำนวนข่าวที่ต้องการดึง
        
    Returns:
        list: รายการข่าวที่ดึงมาได้ หรือ list ว่างถ้าไม่สามารถดึงได้
    """
    try:
        import xml.etree.ElementTree as ET
        
        # ส่งคำขอไปยังเว็บไซต์
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(rss_url, headers=headers, timeout=10)
        
        # ตรวจสอบสถานะการตอบกลับ
        if response.status_code != 200:
            return []
            
        # แปลงข้อมูล XML เป็น ElementTree
        root = ET.fromstring(response.content)
        
        # ดึงข้อมูลข่าว
        news_items = []
        
        # กรณี RSS 2.0
        if root.tag == 'rss':
            channel = root.find('channel')
            items = channel.findall('item')
            
            for item in items[:limit]:
                title = item.find('title').text if item.find('title') is not None else "ไม่มีหัวข้อ"
                link = item.find('link').text if item.find('link') is not None else "#"
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else "ไม่ระบุวันที่"
                description = item.find('description').text if item.find('description') is not None else "ไม่มีคำอธิบาย"
                
                news_items.append({
                    'title': title,
                    'link': link,
                    'pub_date': pub_date,
                    'description': description
                })
        
        # กรณี Atom
        elif root.tag.endswith('feed'):
            namespace = root.tag.split('}')[0] + '}'
            items = root.findall(f'{namespace}entry')
            
            for item in items[:limit]:
                title = item.find(f'{namespace}title').text if item.find(f'{namespace}title') is not None else "ไม่มีหัวข้อ"
                link = item.find(f'{namespace}link').get('href') if item.find(f'{namespace}link') is not None else "#"
                pub_date = item.find(f'{namespace}updated').text if item.find(f'{namespace}updated') is not None else "ไม่ระบุวันที่"
                description = item.find(f'{namespace}summary').text if item.find(f'{namespace}summary') is not None else "ไม่มีคำอธิบาย"
                
                news_items.append({
                    'title': title,
                    'link': link,
                    'pub_date': pub_date,
                    'description': description
                })
        
        return news_items
        
    except Exception as e:
        print(f"Error getting news from RSS: {str(e)}")
        return []