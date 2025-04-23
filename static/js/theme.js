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
    
    // ปรับ class ของ Navbar ตามธีม
    const navbar = document.getElementById('mainNav');
    if (navbar) {
        if (theme === 'dark') {
            navbar.classList.add('navbar-dark');
            navbar.classList.remove('navbar-light');
        } else {
            navbar.classList.add('navbar-light');
            navbar.classList.remove('navbar-dark');
        }
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