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
        
        # ถ้าต้องการกรองข่าวที่เกี่ยวกับข้อมูลตัวเลข
        if filter_numerical and headlines:
            print(f"Before AI filtering: {len(headlines)} headlines")
            
            # ลองใช้ AI กรองหัวข้อข่าวที่เกี่ยวกับข้อมูลตัวเลข
            try:
                ai_filtered_headlines = ai_helper.filter_headlines_with_ai(headlines)
                
                # ถ้า AI สามารถกรองได้ จะใช้ผลลัพธ์จาก AI
                if ai_filtered_headlines and len(ai_filtered_headlines) > 0:
                    headlines = ai_filtered_headlines
                    print(f"After AI filtering: {len(headlines)} headlines")
                    return headlines[:20]  # คืนค่าแค่ 20 หัวข้อแรก
            except Exception as e:
                print(f"Error using AI for filtering: {str(e)}")
                
            # ถ้า AI ไม่ทำงาน ใช้การกรองแบบปกติแทน
            print("Using regular filtering instead of AI")
            
            numerical_keywords = [
                'เพิ่มขึ้น', 'ลดลง', 'ร้อยละ', 'เปอร์เซ็นต์', '%', 'บาท', 'ล้าน', 'พันล้าน',
                'หมื่นล้าน', 'แสนล้าน', 'ดอลลาร์', 'ยูโร', 'เยน', 'หยวน', 'ปอนด์',
                'ดัชนี', 'ราคา', 'หุ้น', 'ค่าเงิน', 'อัตรา', 'ทอง', 'น้ำมัน', 'GDP',
                'ตลาดหุ้น', 'ตลาดหลักทรัพย์', 'SET', 'ธนาคาร', 'งบประมาณ', 'เศรษฐกิจ',
                'การเงิน', 'สถิติ', 'ตัวเลข', 'จำนวน', 'ผลประกอบการ', 'กำไร', 'ขาดทุน', 
                'รายได้', 'รายจ่าย', 'บัญชี', 'หนี้', 'เงินเฟ้อ', 'ดอกเบี้ย', 'เงินกู้', 
                'ตาราง', 'ข้อมูล', 'สำรวจ', 'ระดับ', 'เปรียบเทียบ', 'อันดับ', 'จัดอันดับ'
            ]
            
            # กรองเฉพาะข่าวที่มีคำสำคัญและตัวเลข
            filtered_headlines = []
            
            for headline in headlines:
                title = headline['title'].lower()
                # ตรวจสอบว่ามีตัวเลขในหัวข้อหรือไม่
                has_number = bool(re.search(r'\d', title))
                
                # ตรวจสอบว่ามีคำสำคัญในหัวข้อหรือไม่
                has_keyword = any(keyword.lower() in title for keyword in numerical_keywords)
                
                # ต้องมีทั้งตัวเลขและคำสำคัญ
                if has_number and has_keyword:
                    filtered_headlines.append(headline)
            
            # ถ้าไม่พบข่าวที่เกี่ยวกับตัวเลขเลย ให้ใช้หัวข้อทั้งหมด
            if not filtered_headlines:
                print("No numerical headlines found with regular filtering, returning all headlines")
                return headlines[:20]
            
            print(f"After regular filtering: {len(filtered_headlines)} headlines")
            headlines = filtered_headlines
        
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
        table_from_regex = None
        
        if use_ai:
            try:
                # สรุปเนื้อหาด้วย AI
                ai_summary = ai_helper.summarize_article_with_ai(text)
                
                # สร้างตารางข้อมูลด้วย AI
                ai_table = ai_helper.extract_numerical_table_with_ai(text)
            except Exception as e:
                print(f"Error using AI for content analysis: {str(e)}")
        
        # ถ้า AI ไม่สามารถสร้างตารางได้ ให้ลองใช้การวิเคราะห์แบบปกติเพื่อสร้างตาราง
        if ai_table is None:
            # สร้างตารางด้วยการวิเคราะห์เนื้อหาแบบปกติ
            table_from_regex = create_table_from_text(text)
        
        # วิเคราะห์หาข้อมูลตัวเลขในเนื้อหาด้วยวิธีปกติ
        numerical_data = extract_numerical_data(text)
        
        # สร้างการตอบกลับที่มีทั้งเนื้อหาและข้อมูลกราฟ
        result = {
            'content': text,
            'chart_data': numerical_data,
            'ai_summary': ai_summary,
            'ai_table': ai_table or table_from_regex
        }
            
        return result
        
    except requests.exceptions.Timeout:
        return "การเชื่อมต่อกับเว็บไซต์หมดเวลา"
    except requests.exceptions.ConnectionError:
        return "ไม่สามารถเชื่อมต่อกับเว็บไซต์"
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}"

def create_table_from_text(text):
    """
    ฟังก์ชันสำหรับสร้างตารางข้อมูลจากเนื้อหา โดยใช้การวิเคราะห์ข้อความแบบปกติ
    
    Args:
        text (str): เนื้อหาที่ต้องการวิเคราะห์
        
    Returns:
        dict: ข้อมูลตารางที่สร้างจากเนื้อหา หรือ None ถ้าไม่สามารถสร้างได้
    """
    if not text:
        return None
    
    # แบ่งเนื้อหาเป็นประโยค
    sentences = re.split(r'[.!?]\s', text)
    
    # เก็บข้อมูลตัวเลขและบริบท
    numeric_sentences = []
    comparison_data = []
    time_series_data = []
    
    # กำหนดคำสำคัญที่มักจะเกี่ยวข้องกับการเปรียบเทียบหรือข้อมูลตาราง
    comparison_keywords = ['เปรียบเทียบ', 'ระหว่าง', 'อัตรา', 'เพิ่มขึ้น', 'ลดลง', 'เปลี่ยนแปลง',
                           'มากกว่า', 'น้อยกว่า', 'สูงกว่า', 'ต่ำกว่า', 'อันดับ', 'ติดตาม', 'วัดผล', 'ประเมิน']
    
    time_keywords = ['ปี', 'เดือน', 'ไตรมาส', 'ครึ่งปี', 'ช่วงเวลา', 'พ.ศ.', 'ค.ศ.']
    
    category_keywords = ['ประเภท', 'หมวดหมู่', 'กลุ่ม', 'หัวข้อ', 'ชนิด', 'แบ่งเป็น', 'แบ่งตาม']
    
    # ค้นหาตาราง HTML ที่อาจมีในเนื้อหา (บางเว็บไซต์มีตารางที่อาจถูกดึงมาด้วย)
    html_tables = re.findall(r'<table[^>]*>(.*?)</table>', text, re.DOTALL)
    if html_tables:
        # ถ้าพบตาราง HTML ให้พยายามแปลงเป็นตารางข้อมูล
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_tables[0], 'html.parser')
            headers = [th.text.strip() for th in soup.find_all('th')]
            
            # ถ้าไม่มีส่วนหัวตาราง ให้ใช้คอลัมน์แรกเป็นส่วนหัว
            if not headers:
                first_row = soup.find('tr')
                if first_row:
                    headers = [td.text.strip() for td in first_row.find_all('td')]
            
            rows = []
            for tr in soup.find_all('tr')[1:] if headers else soup.find_all('tr')[1:]:
                row = [td.text.strip() for td in tr.find_all('td')]
                if row:  # เพิ่มเฉพาะแถวที่ไม่ว่างเปล่า
                    rows.append(row)
            
            if headers and rows:
                return {
                    'headers': headers,
                    'rows': rows,
                    'source': 'html_table'
                }
        except Exception as e:
            print(f"Error parsing HTML table: {str(e)}")
    
    # ตรวจสอบประโยคที่มีข้อมูลตัวเลข
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # ค้นหาตัวเลขในประโยค
        numbers = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)', sentence)
        
        # ถ้าพบตัวเลขหลายตัวในประโยคเดียวกัน อาจเป็นข้อมูลตาราง
        if len(numbers) >= 2:
            # ตรวจสอบว่ามีคำสำคัญเกี่ยวกับการเปรียบเทียบหรือไม่
            has_comparison = any(keyword in sentence.lower() for keyword in comparison_keywords)
            has_time = any(keyword in sentence.lower() for keyword in time_keywords)
            has_category = any(keyword in sentence.lower() for keyword in category_keywords)
            
            # เก็บข้อมูล
            data = {
                'sentence': sentence,
                'numbers': numbers,
                'has_comparison': has_comparison,
                'has_time': has_time,
                'has_category': has_category
            }
            
            numeric_sentences.append(data)
            
            # ถ้ามีการเปรียบเทียบ เก็บไว้สำหรับสร้างตาราง
            if has_comparison:
                comparison_data.append(data)
            
            # ถ้ามีการอ้างอิงช่วงเวลา เก็บไว้สำหรับสร้างตารางข้อมูลย้อนหลัง
            if has_time:
                time_series_data.append(data)
    
    # ถ้าไม่พบข้อมูลตัวเลขที่เพียงพอสำหรับสร้างตาราง
    if len(numeric_sentences) < 3:  # ต้องมีอย่างน้อย 3 รายการจึงจะสร้างตารางได้อย่างมีความหมาย
        return None
    
    # สร้างตารางจากข้อมูลตามประเภท
    
    # 1. ถ้ามีข้อมูลเปรียบเทียบ ให้สร้างตารางเปรียบเทียบ
    if comparison_data:
        # ตรวจสอบว่ามีหัวข้อเปรียบเทียบหรือไม่
        categories = []
        for data in comparison_data:
            # ลองหาคำที่อาจเป็นชื่อหมวดหมู่
            sentence = data['sentence'].lower()
            for keyword in category_keywords:
                if keyword in sentence:
                    # ดึงคำที่อยู่หลังคำสำคัญ
                    match = re.search(f'{keyword}\\s+([\\w\\s]+)', sentence)
                    if match:
                        categories.append(match.group(1).strip())
        
        # ถ้าพบหมวดหมู่ ให้ใช้เป็นส่วนหัวตาราง
        if categories:
            headers = ['รายการ'] + categories
            rows = []
            
            # สร้างแถวข้อมูลจากตัวเลขที่พบ
            for i, data in enumerate(comparison_data[:5]):  # จำกัดจำนวนแถว
                row = [f"ข้อมูล {i+1}"] + data['numbers'][:len(categories)]
                rows.append(row)
            
            return {
                'headers': headers,
                'rows': rows,
                'source': 'comparison_analysis'
            }
    
    # 2. ถ้ามีข้อมูลย้อนหลังตามช่วงเวลา ให้สร้างตารางข้อมูลย้อนหลัง
    if time_series_data:
        # ค้นหาช่วงเวลาที่อาจมีในข้อมูล
        time_periods = []
        for data in time_series_data:
            sentence = data['sentence']
            # ค้นหาปีที่อยู่ในประโยค
            years = re.findall(r'(พ\.ศ\.\s*\d{4}|ค\.ศ\.\s*\d{4}|\d{4})', sentence)
            if years:
                for year in years:
                    if year not in time_periods:
                        time_periods.append(year)
            
            # ค้นหาเดือนหรือไตรมาสที่อยู่ในประโยค
            months = re.findall(r'(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม|ไตรมาส\s*\d|Q\d)', sentence)
            if months:
                for month in months:
                    if month not in time_periods:
                        time_periods.append(month)
        
        # ถ้าพบช่วงเวลา ให้ใช้เป็นส่วนหัวตาราง
        if time_periods:
            headers = ['รายการ'] + time_periods
            rows = []
            
            # สร้างแถวข้อมูลจากตัวเลขที่พบ
            for i, data in enumerate(time_series_data[:5]):  # จำกัดจำนวนแถว
                row = [f"ข้อมูล {i+1}"] + data['numbers'][:len(time_periods)]
                rows.append(row)
            
            return {
                'headers': headers,
                'rows': rows,
                'source': 'time_series_analysis'
            }
    
    # 3. ถ้าไม่มีรูปแบบเฉพาะ ให้สร้างตารางทั่วไปจากข้อมูลตัวเลขที่สำคัญที่สุด
    headers = ['ลำดับ', 'รายละเอียด', 'ค่า']
    rows = []
    
    for i, data in enumerate(numeric_sentences[:10]):  # จำกัดจำนวนแถว
        sentence = data['sentence']
        if len(sentence) > 50:
            sentence = sentence[:47] + '...'
        
        # เลือกตัวเลขที่สำคัญที่สุดในประโยค
        number = data['numbers'][0] if data['numbers'] else "N/A"
        
        row = [str(i+1), sentence, number]
        rows.append(row)
    
    return {
        'headers': headers,
        'rows': rows,
        'source': 'general_analysis'
    }

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
def extract_stock_tables(url):
    """
    ฟังก์ชันสำหรับดึงตารางข้อมูลหุ้นจากเว็บไซต์โดยตรง
    
    Args:
        url (str): URL ของเว็บไซต์ที่ต้องการดึงข้อมูลหุ้น
        
    Returns:
        dict: ข้อมูลตารางที่สกัดได้ หรือ None ถ้าไม่สามารถดึงได้
    """
    try:
        # ส่งคำขอไปยังเว็บไซต์
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # ตรวจสอบสถานะการตอบกลับ
        if response.status_code != 200:
            return None
        
        # ใช้ BeautifulSoup เพื่อแยกวิเคราะห์ HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ตรวจสอบว่ามีตารางหรือไม่
        tables = soup.find_all('table')
        if not tables:
            return None
            
        # วิเคราะห์เว็บไซต์ประเภทต่างๆ
        
        # ตรวจสอบว่าเป็นเว็บไซต์ set.or.th
        if "set.or.th" in url or "marketdata" in url:
            return extract_set_data(soup)
        
        # ตรวจสอบว่าเป็นเว็บไซต์ข้อมูลทอง
        if "goldtraders" in url or "gold" in url:
            return extract_gold_data(soup)
            
        # ตรวจสอบว่าเป็นเว็บไซต์อัตราแลกเปลี่ยน
        if "exchange" in url or "currency" in url or "fx" in url:
            return extract_exchange_rate_data(soup)
            
        # ถ้าไม่ตรงกับเงื่อนไขข้างต้น ทดลองดึงข้อมูลจากตารางทั่วไป
        return extract_general_table_data(soup)
            
    except Exception as e:
        print(f"Error extracting stock tables from {url}: {str(e)}")
        return None

def extract_set_data(soup):
    """
    ฟังก์ชันสำหรับดึงข้อมูลจากเว็บไซต์ตลาดหลักทรัพย์
    
    Args:
        soup (BeautifulSoup): BeautifulSoup object ที่มีเนื้อหาเว็บไซต์
        
    Returns:
        dict: ข้อมูลหุ้นที่สกัดได้ หรือ None ถ้าไม่สามารถดึงได้
    """
    try:
        # ขั้นตอนที่ 1: ลองค้นหาข้อมูล SET จาก class เฉพาะของเว็บ set.or.th
        set_container = soup.find('div', {'class': 'market-index-overview-SETMAI'})
        if set_container:
            # พบข้อมูล SET ในรูปแบบพิเศษ
            return extract_set_special_format(set_container)
        
        # ขั้นตอนที่ 2: ตรวจสอบหาตารางทั่วไป
        tables = soup.find_all('table', {'class': ['table', 'table-info', 'table-hover', 'table-responsive']})
        
        if not tables:
            # ลองค้นหาด้วยรูปแบบอื่น
            tables = soup.find_all('table')
            
        if not tables:
            # ลองค้นหาด้วย class ที่มักใช้ในข้อมูลหุ้น
            divs = soup.find_all('div', {'class': ['table', 'stock-table', 'market-table', 'quotes-table']})
            if divs:
                for div in divs:
                    tables_in_div = div.find_all('table')
                    if tables_in_div:
                        tables = tables_in_div
                        break
        
        if not tables:
            # ลองหาข้อมูลในรูปแบบที่ไม่ใช่ตาราง แต่มีโครงสร้างข้อมูลที่คล้ายตาราง
            stock_items = soup.find_all('div', {'class': ['market-overview-item', 'stock-item', 'index-item']})
            if stock_items and len(stock_items) > 0:
                return extract_set_items_format(stock_items)
            return None
            
        # เลือกตารางที่น่าจะมีข้อมูลหุ้นมากที่สุด
        target_table = None
        max_rows = 0
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > max_rows:
                max_rows = len(rows)
                target_table = table
        
        if not target_table:
            return None
            
        # ดึงข้อมูลจากตาราง
        headers = []
        rows_data = []
        
        # ดึงส่วนหัวตาราง
        header_row = target_table.find('thead')
        if header_row:
            th_elements = header_row.find_all('th')
            if not th_elements:
                th_elements = header_row.find_all('td')
            
            headers = [th.get_text(strip=True) for th in th_elements if th.get_text(strip=True)]
        
        # ถ้าไม่มี thead ลองดูแถวแรกเป็นหัวตารางแทน
        if not headers:
            first_row = target_table.find('tr')
            if first_row:
                th_elements = first_row.find_all('th')
                if not th_elements:
                    th_elements = first_row.find_all('td')
                
                headers = [th.get_text(strip=True) for th in th_elements if th.get_text(strip=True)]
        
        # ดึงข้อมูลแถว
        rows = target_table.find_all('tr')
        start_idx = 0 if not headers else 1
        
        for row in rows[start_idx:]:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            
            # เฉพาะแถวที่มีข้อมูล
            if any(cell for cell in row_data):
                rows_data.append(row_data)
        
        # สร้างตารางข้อมูลในรูปแบบเดียวกับที่ AI สร้าง
        if not headers and rows_data:
            # สร้างส่วนหัวตารางแบบอัตโนมัติ
            headers = [f"Column {i+1}" for i in range(len(rows_data[0]))]
        
        # ข้อมูลที่จะส่งกลับ
        table_data = {
            "headers": headers,
            "rows": rows_data
        }
        
        return table_data
        
    except Exception as e:
        print(f"Error extracting SET data: {str(e)}")
        return None

def extract_set_special_format(container):
    """
    ฟังก์ชันสำหรับดึงข้อมูล SET จากรูปแบบพิเศษของเว็บไซต์ตลาดหลักทรัพย์
    
    Args:
        container (BeautifulSoup element): ส่วนที่บรรจุข้อมูล SET
        
    Returns:
        dict: ข้อมูลดัชนีและราคาหุ้นที่สกัดได้
    """
    try:
        # ดึงข้อมูลดัชนีหลัก
        rows_data = []
        headers = ["ดัชนี", "ล่าสุด", "เปลี่ยนแปลง", "% เปลี่ยนแปลง", "ปริมาณ (พันหุ้น)", "มูลค่า (ล้านบาท)"]
        
        # ดึงข้อมูลในส่วนของ market-overview หรือ market-stats
        market_data = container.find_all('div', {'class': ['market-overview', 'market-stats', 'index-overview', 'index-data']})
        
        # ถ้าไม่พบข้อมูลในรูปแบบที่คาด ลองค้นหาแบบทั่วไป
        if not market_data:
            market_data = container.find_all('div')
        
        for section in market_data:
            # ค้นหาชื่อดัชนี
            index_name = None
            name_element = section.find('div', {'class': ['index-name', 'name', 'title']})
            if name_element:
                index_name = name_element.get_text(strip=True)
            else:
                # ลองค้นหาในรูปแบบอื่น
                header = section.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                if header:
                    index_name = header.get_text(strip=True)
            
            if not index_name:
                continue
                
            # ค้นหาค่าดัชนีล่าสุด
            last_value = None
            value_element = section.find('div', {'class': ['index-value', 'last', 'value', 'price']})
            if value_element:
                last_value = value_element.get_text(strip=True)
            
            # ค้นหาค่าการเปลี่ยนแปลง
            change_value = None
            change_element = section.find('div', {'class': ['change-value', 'change']})
            if change_element:
                change_value = change_element.get_text(strip=True)
            
            # ค้นหาค่าเปอร์เซ็นต์การเปลี่ยนแปลง
            change_percent = None
            percent_element = section.find('div', {'class': ['change-percent', 'percent']})
            if percent_element:
                change_percent = percent_element.get_text(strip=True)
            
            # ค้นหาปริมาณการซื้อขาย
            volume = None
            volume_element = section.find('div', {'class': ['volume', 'vol']})
            if volume_element:
                volume = volume_element.get_text(strip=True)
            
            # ค้นหามูลค่าการซื้อขาย
            value = None
            value_element = section.find('div', {'class': ['trading-value', 'val']})
            if value_element:
                value = value_element.get_text(strip=True)
            
            # สร้างข้อมูลแถว
            row_data = [index_name, last_value, change_value, change_percent, volume, value]
            
            # ตรวจสอบว่ามีข้อมูลในแถวหรือไม่
            if any(cell for cell in row_data if cell is not None):
                # แทนที่ค่า None ด้วยข้อความว่าง
                row_data = [cell if cell is not None else "" for cell in row_data]
                rows_data.append(row_data)
        
        # ตรวจสอบว่าพบข้อมูลหรือไม่
        if not rows_data:
            # ถ้าไม่พบข้อมูลในรูปแบบข้างต้น ลองดึงข้อมูลจากทั้งหน้า
            all_text = container.get_text(strip=True)
            rows_data.append(["ข้อมูลดัชนีตลาดหลักทรัพย์", all_text, "", "", "", ""])
        
        # ส่งกลับข้อมูลในรูปแบบตาราง
        return {
            "headers": headers,
            "rows": rows_data
        }
        
    except Exception as e:
        print(f"Error extracting special SET format: {str(e)}")
        # ส่งกลับข้อมูลพื้นฐานที่พบในข้อผิดพลาด
        return {
            "headers": ["ข้อมูล"],
            "rows": [["ไม่สามารถดึงข้อมูลในรูปแบบพิเศษได้"]]
        }

def extract_set_items_format(items):
    """
    ฟังก์ชันสำหรับดึงข้อมูลจากรายการข้อมูลหุ้นที่ไม่ได้อยู่ในรูปแบบตาราง
    
    Args:
        items (list): รายการ elements ที่มีข้อมูลหุ้นแต่ละตัว
        
    Returns:
        dict: ข้อมูลหุ้นที่สกัดได้ในรูปแบบตาราง
    """
    try:
        headers = ["ชื่อ", "ล่าสุด", "เปลี่ยนแปลง", "% เปลี่ยนแปลง"]
        rows_data = []
        
        for item in items:
            name = None
            last_value = None
            change = None
            percent = None
            
            # ค้นหาชื่อ
            name_element = item.find('div', {'class': ['name', 'title', 'symbol']})
            if name_element:
                name = name_element.get_text(strip=True)
            
            # ค้นหาค่าล่าสุด
            last_element = item.find('div', {'class': ['last', 'value', 'price']})
            if last_element:
                last_value = last_element.get_text(strip=True)
            
            # ค้นหาค่าเปลี่ยนแปลง
            change_element = item.find('div', {'class': ['change', 'change-value']})
            if change_element:
                change = change_element.get_text(strip=True)
            
            # ค้นหาเปอร์เซ็นต์เปลี่ยนแปลง
            percent_element = item.find('div', {'class': ['percent', 'change-percent']})
            if percent_element:
                percent = percent_element.get_text(strip=True)
            
            # สร้างข้อมูลแถว
            row_data = [name, last_value, change, percent]
            
            # ตรวจสอบว่ามีข้อมูลในแถวหรือไม่
            if any(cell for cell in row_data if cell is not None):
                # แทนที่ค่า None ด้วยข้อความว่าง
                row_data = [cell if cell is not None else "" for cell in row_data]
                rows_data.append(row_data)
        
        # ส่งกลับข้อมูลในรูปแบบตาราง
        return {
            "headers": headers,
            "rows": rows_data
        }
        
    except Exception as e:
        print(f"Error extracting SET items format: {str(e)}")
        return None

def extract_gold_data(soup):
    """
    ฟังก์ชันสำหรับดึงข้อมูลราคาทองจากเว็บไซต์
    
    Args:
        soup (BeautifulSoup): BeautifulSoup object ที่มีเนื้อหาเว็บไซต์
        
    Returns:
        dict: ข้อมูลราคาทองที่สกัดได้ หรือ None ถ้าไม่สามารถดึงได้
    """
    try:
        # ดึงข้อมูลเฉพาะสำหรับราคาทอง
        gold_table = None
        tables = soup.find_all('table')
        
        for table in tables:
            text = table.get_text().lower()
            if 'ทอง' in text or 'บาท' in text or 'รูปพรรณ' in text or 'ขาย' in text:
                gold_table = table
                break
                
        if not gold_table:
            return None
            
        # ดึงข้อมูลจากตาราง
        headers = []
        rows_data = []
        
        # ดึงส่วนหัวตาราง
        header_row = gold_table.find('thead')
        if header_row:
            th_elements = header_row.find_all('th')
            if not th_elements:
                th_elements = header_row.find_all('td')
            
            headers = [th.get_text(strip=True) for th in th_elements if th.get_text(strip=True)]
        
        # ถ้าไม่มี thead ลองดูแถวแรกเป็นหัวตารางแทน
        if not headers:
            first_row = gold_table.find('tr')
            if first_row:
                th_elements = first_row.find_all('th')
                if not th_elements:
                    th_elements = first_row.find_all('td')
                
                headers = [th.get_text(strip=True) for th in th_elements if th.get_text(strip=True)]
        
        # ดึงข้อมูลแถว
        rows = gold_table.find_all('tr')
        start_idx = 0 if not headers else 1
        
        for row in rows[start_idx:]:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            
            # เฉพาะแถวที่มีข้อมูล
            if any(cell for cell in row_data):
                rows_data.append(row_data)
        
        # สร้างตารางข้อมูลในรูปแบบเดียวกับที่ AI สร้าง
        if not headers and rows_data:
            # สร้างส่วนหัวตารางแบบอัตโนมัติ
            headers = [f"Column {i+1}" for i in range(len(rows_data[0]))]
        
        # ข้อมูลที่จะส่งกลับ
        table_data = {
            "headers": headers,
            "rows": rows_data
        }
        
        return table_data
        
    except Exception as e:
        print(f"Error extracting gold data: {str(e)}")
        return None

def extract_exchange_rate_data(soup):
    """
    ฟังก์ชันสำหรับดึงข้อมูลอัตราแลกเปลี่ยนจากเว็บไซต์
    
    Args:
        soup (BeautifulSoup): BeautifulSoup object ที่มีเนื้อหาเว็บไซต์
        
    Returns:
        dict: ข้อมูลอัตราแลกเปลี่ยนที่สกัดได้ หรือ None ถ้าไม่สามารถดึงได้
    """
    try:
        # ดึงข้อมูลเฉพาะสำหรับอัตราแลกเปลี่ยน
        exchange_table = None
        tables = soup.find_all('table')
        
        for table in tables:
            text = table.get_text().lower()
            if 'usd' in text or 'eur' in text or 'jpy' in text or 'currency' in text or 'สกุลเงิน' in text:
                exchange_table = table
                break
                
        if not exchange_table:
            return None
            
        # ดึงข้อมูลจากตาราง
        headers = []
        rows_data = []
        
        # ดึงส่วนหัวตาราง
        header_row = exchange_table.find('thead')
        if header_row:
            th_elements = header_row.find_all('th')
            if not th_elements:
                th_elements = header_row.find_all('td')
            
            headers = [th.get_text(strip=True) for th in th_elements if th.get_text(strip=True)]
        
        # ถ้าไม่มี thead ลองดูแถวแรกเป็นหัวตารางแทน
        if not headers:
            first_row = exchange_table.find('tr')
            if first_row:
                th_elements = first_row.find_all('th')
                if not th_elements:
                    th_elements = first_row.find_all('td')
                
                headers = [th.get_text(strip=True) for th in th_elements if th.get_text(strip=True)]
        
        # ดึงข้อมูลแถว
        rows = exchange_table.find_all('tr')
        start_idx = 0 if not headers else 1
        
        for row in rows[start_idx:]:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            
            # เฉพาะแถวที่มีข้อมูล
            if any(cell for cell in row_data):
                rows_data.append(row_data)
        
        # สร้างตารางข้อมูลในรูปแบบเดียวกับที่ AI สร้าง
        if not headers and rows_data:
            # สร้างส่วนหัวตารางแบบอัตโนมัติ
            headers = [f"Column {i+1}" for i in range(len(rows_data[0]))]
        
        # ข้อมูลที่จะส่งกลับ
        table_data = {
            "headers": headers,
            "rows": rows_data
        }
        
        return table_data
        
    except Exception as e:
        print(f"Error extracting exchange rate data: {str(e)}")
        return None

def extract_general_table_data(soup):
    """
    ฟังก์ชันสำหรับดึงข้อมูลจากตารางทั่วไป
    
    Args:
        soup (BeautifulSoup): BeautifulSoup object ที่มีเนื้อหาเว็บไซต์
        
    Returns:
        dict: ข้อมูลตารางที่สกัดได้ หรือ None ถ้าไม่สามารถดึงได้
    """
    try:
        # ค้นหาตารางที่มีตัวเลขมากที่สุด
        tables = soup.find_all('table')
        
        if not tables:
            return None
            
        best_table = None
        max_numeric_cells = 0
        
        for table in tables:
            numeric_count = 0
            cells = table.find_all(['td', 'th'])
            
            for cell in cells:
                text = cell.get_text(strip=True)
                # ตรวจสอบว่ามีตัวเลขหรือไม่
                if re.search(r'\d+\.?\d*', text):
                    numeric_count += 1
            
            if numeric_count > max_numeric_cells:
                max_numeric_cells = numeric_count
                best_table = table
        
        if not best_table:
            return None
            
        # ดึงข้อมูลจากตาราง
        headers = []
        rows_data = []
        
        # ดึงส่วนหัวตาราง
        header_row = best_table.find('thead')
        if header_row:
            th_elements = header_row.find_all('th')
            if not th_elements:
                th_elements = header_row.find_all('td')
            
            headers = [th.get_text(strip=True) for th in th_elements if th.get_text(strip=True)]
        
        # ถ้าไม่มี thead ลองดูแถวแรกเป็นหัวตารางแทน
        if not headers:
            first_row = best_table.find('tr')
            if first_row:
                th_elements = first_row.find_all('th')
                if not th_elements:
                    th_elements = first_row.find_all('td')
                
                headers = [th.get_text(strip=True) for th in th_elements if th.get_text(strip=True)]
        
        # ดึงข้อมูลแถว
        rows = best_table.find_all('tr')
        start_idx = 0 if not headers else 1
        
        for row in rows[start_idx:]:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            
            # เฉพาะแถวที่มีข้อมูล
            if any(cell for cell in row_data):
                rows_data.append(row_data)
        
        # สร้างตารางข้อมูลในรูปแบบเดียวกับที่ AI สร้าง
        if not headers and rows_data:
            # สร้างส่วนหัวตารางแบบอัตโนมัติ
            headers = [f"Column {i+1}" for i in range(len(rows_data[0]))]
        
        # ข้อมูลที่จะส่งกลับ
        table_data = {
            "headers": headers,
            "rows": rows_data
        }
        
        return table_data
        
    except Exception as e:
        print(f"Error extracting general table data: {str(e)}")
        return None

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