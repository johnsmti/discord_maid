from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Maid Cafe Bot is Online!"

def run():
    # Render Free แนะนำให้ใช้พอร์ต 10000
    app.run(host='0.0.0.0', port=10000)

# ชื่อฟังก์ชันต้องเป็น server_on เพื่อให้ main.py เรียกใช้ได้
def server_on():
    t = Thread(target=run)
    t.start()
