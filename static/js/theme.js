// ฟังก์ชันสำหรับตั้งค่าธีม
function setTheme(theme) {
    // บันทึกธีมลงใน localStorage และส่งไปยังเซิร์ฟเวอร์
    localStorage.setItem('theme', theme);
    
    // ส่งข้อมูลธีมไปยังเซิร์ฟเวอร์
    const formData = new FormData();
    formData.append('theme', theme);
    
    fetch('/set-theme', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            if (theme === 'auto') {
                applySystemTheme();
            } else {
                applyTheme(theme);
            }
        }
    })
    .catch(error => {
        console.error('Error setting theme:', error);
        // หากไม่สามารถส่งไปยังเซิร์ฟเวอร์ได้ ก็ยังใช้ client-side fallback
        if (theme === 'auto') {
            applySystemTheme();
        } else {
            applyTheme(theme);
        }
    });
}

// ฟังก์ชันสำหรับใช้ธีมตามการตั้งค่าของระบบ
function applySystemTheme() {
    // ตรวจสอบว่าระบบใช้ธีมมืดหรือไม่
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // ใช้ธีมตามการตั้งค่าของระบบ
    if (prefersDarkScheme) {
        applyTheme('dark');
    } else {
        applyTheme('light');
    }
}

// ฟังก์ชันสำหรับใช้ธีมที่เลือก
function applyTheme(theme) {
    // กำหนดธีมให้กับ HTML element
    document.documentElement.setAttribute('data-bs-theme', theme);
    
    // ลบ style element เก่าออกก่อน (ถ้ามี)
    const oldStyle = document.getElementById('theme-specific-styles');
    if (oldStyle) {
        oldStyle.remove();
    }
    
    // ปรับ class ของ Navbar ตามธีม
    const navbar = document.getElementById('mainNav');
    if (navbar) {
        // ตั้งค่า CSS สำหรับลิงก์
        let cssContent = '';
        
        if (theme === 'dark') {
            navbar.classList.add('navbar-dark');
            navbar.classList.remove('navbar-light');
            
            // สำหรับธีมมืด กำหนดสีข้อความเป็นสีขาว
            const navLinks = document.querySelectorAll('.menu-link');
            navLinks.forEach(link => {
                link.style.color = 'rgba(255, 255, 255, 0.85)';
            });
            
            // CSS สำหรับธีมมืด
            cssContent = `
                .navbar-dark .menu-link:hover, 
                .navbar-dark .menu-link.active {
                    color: white !important;
                    background-color: rgba(255, 255, 255, 0.1);
                }
            `;
        } else {
            navbar.classList.add('navbar-light');
            navbar.classList.remove('navbar-dark');
            
            // สำหรับธีมสว่าง กำหนดสีข้อความเป็นสีดำ
            const navLinks = document.querySelectorAll('.menu-link');
            navLinks.forEach(link => {
                link.style.color = '#333333';
            });
            
            // CSS สำหรับธีมสว่าง
            cssContent = `
                .navbar-light .menu-link:hover, 
                .navbar-light .menu-link.active {
                    color: var(--primary-color) !important;
                    background-color: rgba(0, 0, 0, 0.05);
                }
                
                /* ปรับปุ่ม navbar-toggler ในธีมสว่าง */
                .navbar-light .navbar-toggler {
                    color: rgba(0, 0, 0, 0.55);
                    border-color: rgba(0, 0, 0, 0.1);
                }
                
                .navbar-light .navbar-toggler-icon {
                    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='rgba%280, 0, 0, 0.55%29' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e");
                }
            `;
        }
        
        // สร้าง style element ใหม่
        const style = document.createElement('style');
        style.id = 'theme-specific-styles';
        style.textContent = cssContent;
        document.head.appendChild(style);
    }
}

// เมื่อโหลดหน้าเพจเสร็จ ปรับแต่ง UI ตามธีมที่ได้รับจาก server
document.addEventListener('DOMContentLoaded', function() {
    // ดูว่าธีมปัจจุบันที่ได้รับจาก server คืออะไร ผ่าน data-bs-theme attribute
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    
    // บันทึกลงใน localStorage เพื่อความเข้ากันได้กับโค้ดเดิม
    if (currentTheme) {
        localStorage.setItem('theme', currentTheme);
    }
    
    // ปรับแต่ง UI เพิ่มเติม (เช่น สไตล์ของเมนู) ตามธีมปัจจุบัน
    applyTheme(currentTheme || 'dark');
});