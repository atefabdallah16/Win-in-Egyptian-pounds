import os
import psycopg2
from flask import Flask, render_template, request, redirect, session
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.secret_key = "secret123"

DATABASE_URL = os.environ.get("DATABASE_URL") or "postgresql://postgres:a01027625506@localhost:5432/mydb"

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            name TEXT,
            phone TEXT,
            booking_datetime TIMESTAMP,
            status TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def cancel_expired():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, booking_datetime FROM bookings WHERE status='active'")
    rows = cur.fetchall()
    now = datetime.now(ZoneInfo("Africa/Cairo"))
    for row in rows:
        booking_time = row[1].replace(tzinfo=ZoneInfo("Africa/Cairo"))
        if now > booking_time + timedelta(minutes=15):
            cur.execute("UPDATE bookings SET status='cancelled' WHERE id=%s", (row[0],))
    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def home():
    cancel_expired()
    conn = get_db()
    cur = conn.cursor()
    now = datetime.now(ZoneInfo("Africa/Cairo"))
    today_str = now.strftime("%Y-%m-%d")
    cur.execute("""
        SELECT TO_CHAR(booking_datetime, 'HH24:MI') 
        FROM bookings 
        WHERE status='active' AND TO_CHAR(booking_datetime, 'YYYY-MM-DD') = %s
    """, (today_str,))
    booked_times = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return render_template("index.html", booked_times=booked_times)

@app.route("/book", methods=["POST"])
def book():
    name = request.form["name"]
    phone = request.form["phone"]
    time_str = request.form["time"]
    now = datetime.now(ZoneInfo("Africa/Cairo"))
    target_date = now.strftime("%Y-%m-%d")
    booking_datetime = datetime.strptime(target_date + " " + time_str, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Africa/Cairo"))

    if booking_datetime < now:
        return "❌ عذراً، هذا الوقت قد مضى بالفعل اليوم"

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE booking_datetime=%s AND status='active'", (booking_datetime,))
    if cur.fetchone():
        return "❌ هذا الموعد محجوز بالفعل"

    cur.execute("INSERT INTO bookings (name, phone, booking_datetime, status) VALUES (%s, %s, %s, %s)",
                (name, phone, booking_datetime, "active"))
    conn.commit()
    cur.close()
    conn.close()
    return render_template("success.html")

@app.route("/public_schedule")
def public_schedule():
    cancel_expired()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT booking_datetime FROM bookings WHERE status='active' ORDER BY booking_datetime")
    bookings = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("public_schedule.html", bookings=bookings)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == "101010":
            session["admin"] = True
            return redirect("/admin")
        return "❌ الباسورد خطأ"
    return render_template("login.html")

@app.route("/admin")
def admin():
    if not session.get("admin"): return redirect("/login")
    cancel_expired()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, phone, booking_datetime, status FROM bookings ORDER BY booking_datetime")
    bookings = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin.html", bookings=bookings)

@app.route("/delete_all")
def delete_all():
    if not session.get("admin"): return redirect("/login")
    conn = get_db()
    cur = conn.cursor(); cur.execute("DELETE FROM bookings"); conn.commit()
    cur.close(); conn.close()
    return redirect("/admin")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
    