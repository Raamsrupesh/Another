import streamlit as st
import sqlite3
import hashlib
import extra_streamlit_components as stx  # pip install extra-streamlit-components

# Create persistent cookie manager
cookie_manager = stx.CookieManager()

# SQLite setup
conn = sqlite3.connect("rolls.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (device_id TEXT PRIMARY KEY, roll_no TEXT)")
conn.commit()

# Generate or load existing unique device ID cookie
device_cookie = cookie_manager.get(cookie="device_id")

if not device_cookie:
    # create a permanent unique ID
    device_cookie = hashlib.sha256(st.session_state.get("run_id", str(st.session_state)).encode()).hexdigest()
    cookie_manager.set("device_id", device_cookie, key="user_cookie", expires_at=None)

# Now check DB for this device ID
cur.execute("SELECT roll_no FROM users WHERE device_id=?", (device_cookie,))
record = cur.fetchone()

if record:
    st.success(f"Your roll number is {record[0]} (locked permanently).")
else:
    roll = st.text_input("Enter your roll number:")
    if st.button("Save"):
        cur.execute("INSERT INTO users (device_id, roll_no) VALUES (?, ?)", (device_cookie, roll))
        conn.commit()
        st.success("Roll number saved permanently!")
