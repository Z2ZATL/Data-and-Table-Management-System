from flask import Flask, render_template, request

app = Flask(__name__)

# หน้าแรกแสดงฟอร์มกรอกชื่อ
@app.route("/")
def index():
    return render_template("index.html")

# รับค่าจากฟอร์มและแสดงผล
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    return f"ยินดีต้อนรับ, {name}"

if __name__ == "__main__":
    app.run(debug=True)
