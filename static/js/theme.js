// ฟังก์ชันสำหรับตั้งค่าธีม
function setTheme(theme) {
    // บันทึกธีมลงใน localStorage
    localStorage.setItem('theme', theme);
    
    // ใช้ธีมที่เลือก
    if (theme === 'auto') {
        applySystemTheme();
    } else {
        applyTheme(theme);
    }
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
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.style.color = 'rgba(255, 255, 255, 0.85)';
            });
            
            // CSS สำหรับธีมมืด
            cssContent = `
                .navbar-dark .nav-link:hover, 
                .navbar-dark .nav-link.active {
                    color: white !important;
                    background-color: rgba(255, 255, 255, 0.1);
                }
            `;
        } else {
            navbar.classList.add('navbar-light');
            navbar.classList.remove('navbar-dark');
            
            // สำหรับธีมสว่าง กำหนดสีข้อความเป็นสีดำ
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.style.color = '#333333';
            });
            
            // CSS สำหรับธีมสว่าง
            cssContent = `
                .navbar-light .nav-link:hover, 
                .navbar-light .nav-link.active {
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

// เมื่อโหลดหน้าเพจเสร็จ ให้ตรวจสอบและใช้ธีมที่บันทึกไว้
document.addEventListener('DOMContentLoaded', function() {
    // ดึงค่าธีมที่บันทึกไว้ใน localStorage
    const savedTheme = localStorage.getItem('theme');
    
    // ถ้ามีการบันทึกธีมไว้ ให้ใช้ธีมนั้น
    if (savedTheme) {
        applyTheme(savedTheme);
    } 
    // ถ้าไม่มีธีมที่บันทึกไว้ แต่มีการตั้งค่าให้ใช้ธีมตามระบบ ให้ตรวจสอบธีมของระบบ
    else if (localStorage.getItem('theme') === 'auto') {
        applySystemTheme();
    }
    // ถ้าไม่มีการตั้งค่าธีมเลย ให้ใช้ธีมมืดเป็นค่าเริ่มต้น
    else {
        localStorage.setItem('theme', 'dark');
        applyTheme('dark');
    }
});