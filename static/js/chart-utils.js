// ฟังก์ชันสำหรับสร้างกราฟจากข้อมูลตาราง
function createChart(chartId, tableData) {
    const chartContainer = document.getElementById(chartId);
    
    // หากมีการแสดงกราฟอยู่แล้ว ให้ซ่อนกราฟและหยุดการทำงาน
    if (chartContainer.style.display !== 'none') {
        chartContainer.style.display = 'none';
        return;
    }
    
    // แสดงกราฟ
    chartContainer.style.display = 'block';
    
    // กำหนดข้อมูลสำหรับกราฟ
    const headers = tableData.headers;
    const rows = tableData.rows;
    
    // ตรวจสอบประเภทข้อมูลเพื่อเลือกกราฟที่เหมาะสม
    let chartType = 'bar';
    let datasets = [];
    
    // สร้าง labels จากคอลัมน์แรก (ถ้ามี)
    let labels = [];
    if (rows.length > 0) {
        if (rows[0].length > 1) {
            // กรณีมีมากกว่า 1 คอลัมน์ ใช้คอลัมน์แรกเป็น labels
            labels = rows.map(row => row[0]);
            
            // สร้าง datasets จากคอลัมน์ที่เหลือ
            for (let i = 1; i < headers.length; i++) {
                datasets.push({
                    label: headers[i],
                    data: rows.map(row => parseFloat(row[i]) || 0),
                    backgroundColor: getRandomColor(i),
                    borderColor: getRandomColor(i),
                    borderWidth: 1
                });
            }
        } else {
            // กรณีมีเพียง 1 คอลัมน์ ใช้ headers เป็น labels
            labels = headers;
            datasets.push({
                label: 'ข้อมูล',
                data: rows.map(row => parseFloat(row[0]) || 0),
                backgroundColor: rows.map((_, i) => getRandomColor(i)),
                borderWidth: 1
            });
            chartType = 'pie';
        }
    }
    
    // สร้างกราฟใหม่
    new Chart(chartContainer, {
        type: chartType,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: (chartType === 'pie') ? {} : {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// ฟังก์ชันสร้างสีแบบสุ่ม
function getRandomColor(index) {
    // กำหนดสีที่ใช้บ่อยสำหรับกราฟ
    const colors = [
        'rgba(75, 192, 192, 0.7)',
        'rgba(255, 99, 132, 0.7)',
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(153, 102, 255, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(199, 199, 199, 0.7)',
        'rgba(83, 102, 255, 0.7)',
        'rgba(40, 167, 69, 0.7)',
        'rgba(220, 53, 69, 0.7)',
    ];
    
    // ใช้สีในลิสต์ถ้าอยู่ในช่วงที่มี
    if (index < colors.length) {
        return colors[index];
    }
    
    // ถ้าไม่มีในลิสต์ สร้างสีแบบสุ่ม
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    return `rgba(${r}, ${g}, ${b}, 0.7)`;
}