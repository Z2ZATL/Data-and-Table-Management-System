import trafilatura
import requests

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

def get_data_from_website(url):
    """
    ฟังก์ชันนี้ใช้สำหรับดึงข้อมูลจากเว็บไซต์และจัดรูปแบบให้เป็นคำอธิบายสั้นๆ
    
    Args:
        url (str): URL ของเว็บไซต์ที่ต้องการดึงข้อมูล
        
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
        
        # แทนที่บรรทัดว่างซ้ำด้วยบรรทัดว่างเดียว
        text = text.replace('\n\n\n', '\n\n')
        
        # เพิ่มบรรทัดว่างหลังจุด เพื่อให้อ่านง่ายขึ้น
        text = text.replace('. ', '.\n')
        
        # แทนที่เครื่องหมายอื่นๆ เพื่อให้อ่านง่ายขึ้น
        text = text.replace('! ', '!\n')
        text = text.replace('? ', '?\n')
        
        # จำกัดความยาวของเนื้อหา
        if len(text) > 2000:
            # ตัดที่ประโยคที่สมบูรณ์เพื่อให้อ่านง่ายขึ้น
            cutoff = text[:1997].rfind('.')
            if cutoff > 1000:  # ถ้าพบจุดในช่วงที่เหมาะสม
                text = text[:cutoff+1] + "..."
            else:
                text = text[:1997] + "..."
            
        return text
        
    except requests.exceptions.Timeout:
        return "การเชื่อมต่อกับเว็บไซต์หมดเวลา"
    except requests.exceptions.ConnectionError:
        return "ไม่สามารถเชื่อมต่อกับเว็บไซต์"
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}"

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