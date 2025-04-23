# แสดงการใช้ list และ loop
names = ["Alice", "Bob", "Charlie"]

for name in names:
    print(f"สวัสดี {name}")

# การใช้ dictionary
person = {"name": "Alice", "age": 25}
print(f"{person['name']} อายุ {person['age']} ปี")

# ฟังก์ชันเบื้องต้น
def greet(name):
    return f"สวัสดี {name}"

print(greet("Dora"))
