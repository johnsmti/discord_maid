from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Maid Cafe Bot is Online!"

def run():
    # กำหนดพอร์ต 8080 ซึ่งเป็นพอร์ตมาตรฐานที่ Hosting มักใช้
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()