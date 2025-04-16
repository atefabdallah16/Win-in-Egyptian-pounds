from flask import Flask, render_template, request
import json
import os

app = Flask(__name__)
DATA_FILE = 'data.json'

# لو ملف البيانات مش موجود، اعمله
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    user_ip = request.remote_addr
    data = load_data()

    # سجل الزيارة وزوّد النقاط
    if user_ip in data:
        data[user_ip] += 1
    else:
        data[user_ip] = 1

    save_data(data)
    points = data[user_ip]

    return render_template('index.html', points=points)

if __name__ == '__main__':
    app.run(debug=True)
