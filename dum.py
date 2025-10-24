import streamlit as st
import pandas as pd
from datetime import datetime
import os
from streamlit.runtime.scriptrunner import get_script_run_ctx
import hashlib
import sqlite3
import uuid
from streamlit_js_eval import streamlit_js_eval

DB_PATH = "attendance.sqlite"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            roll_number TEXT PRIMARY KEY,
            device_id TEXT,
            mark_date TEXT,
            mark_time TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_bindings (
            roll_number TEXT PRIMARY KEY,
            device_id TEXT,
            name TEXT
        )
    """)
    return conn

# Get (or create) persistent device ID via JS (stored in browser localStorage)
device_id = streamlit_js_eval(
    js_expressions=[
        "localStorage.getItem('deviceID') || (function(){ localStorage.setItem('deviceID', crypto.randomUUID()); return localStorage.getItem('deviceID'); })()"
    ],
    key="device_id_js"
)[0]

tab1, tab2, tab3 = st.tabs(['Register/Login', 'Student/CR', 'Ask Permission'])

# ===== Unique session ID generation function =====
def get_session_id():
    ctx = get_script_run_ctx()
    if ctx and ctx.session_id:
        return hashlib.sha256(ctx.session_id.encode()).hexdigest()
    else:
        return hashlib.sha256(str(datetime.now()).encode()).hexdigest()

# ====== Constants/Initializations ======
ATTENDANCE_FILE = 'attendance.csv'
options = [
    'X1', 'X2', 'X3', 'X4', 'X5', 'X6', 'X7', 'X8', 'X9', 'Y0', 'Y1', 'Y2', 'Y3',
    'Y4', 'Y5', 'Y6', 'Y7', 'Y8', 'Y9', 'Z0', 'Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6',
    'Z7', 'Z8', 'Z9', 'AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ',
    'AK', 'AL', 'AM', 'AN', 'AO', 'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AV', 'AW',
    'AX', 'AY', 'AZ', 'BA', 'BB', 'BC', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ',
    'BK', 'BL', 'BM', 'BN', 'BO', 'BP', 'BQ', 'BR', 'BS', 'BT', 'BU', 'BV', 'BW',
    'BX', 'BY', 'BZ'
]
passwords = {rn: 'In' + rn + '@123' for rn in options}
rep_password = 'REP123'

# ====== Create attendance file if needed ======
if not os.path.exists(ATTENDANCE_FILE):
    df = pd.DataFrame(columns=['SessionID', 'Name', 'Date'])
    df.to_csv(ATTENDANCE_FILE, index=False)

attendance_df = pd.read_csv(ATTENDANCE_FILE)

# ====== Initialize session context ======
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = get_session_id()
if 'user' not in st.session_state:
    st.session_state['user'] = None

def check_device_binding(roll_number):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT device_id FROM user_bindings WHERE roll_number=?", (roll_number,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0] == device_id
    return False

with tab1:
    st.title("Registration for Students!!")
    Name = st.text_input("Enter your name: ", placeholder='E.g: RAAMA')
    Roll_no = st.text_input("Enter Roll Number: ", placeholder='E.g: BI')
    if st.button('Submit'):
        if Roll_no not in options:
            st.error("YOU ARE NOT A MEMBER OF CLASS")
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            # Check if roll_number is already bound to any device
            cur.execute("SELECT device_id FROM user_bindings WHERE roll_number=?", (Roll_no,))
            roll_row = cur.fetchone()
            # Check if device_id is already bound to any roll_number
            cur.execute("SELECT roll_number FROM user_bindings WHERE device_id=?", (device_id,))
            device_row = cur.fetchone()
            if roll_row:
                if roll_row[0] == device_id:
                    st.warning("You are already registered with this roll number on this device.")
                else:
                    st.error("ERROR: Roll number is already used by another device.")
            elif device_row:
                st.error("ERROR: This device is already bound to another roll number.")
            else:
                # Bind roll number to this device
                try:
                    cur.execute("INSERT INTO user_bindings (roll_number, device_id, name) VALUES (?, ?, ?)", (Roll_no, device_id, Name))
                    conn.commit()
                    st.success("**ACCESS GRANTED** (Registered to this device)")
                except sqlite3.IntegrityError:
                    st.error("THIS ROLL NUMBER IS ALREADY USED!!")
            conn.close()

with tab2:
    st.title('CSE Attendance Checker!!')
    st.header('Enter the following details:')

    # Security check: Ensure roll_no is entered and bound to this device
    if not Roll_no or not check_device_binding(Roll_no):
        st.error("Please register first and ensure your roll number is bound to this device.")
    else:
        role = st.radio('Select Your Role:', ['Student', 'Class Representative'])

        if role == 'Student':
            try:
                from streamlit_geolocation import streamlit_geolocation
                location = streamlit_geolocation()
            except ImportError:
                location = {}
                st.warning('streamlit_geolocation package not found. Location fetch will not work!')

            selected = st.selectbox('Who are You?', [Roll_no])
            password = st.text_input("Enter Secret Password:", type='password')

            if st.button('Mark Present?'):
                today = datetime.today().strftime('%Y-%m-%d')
                input_time = datetime.now().strftime("%H:%M:%S")

                if st.session_state['user'] is None:
                    # First mark for this browser session, user selection is saved
                    if passwords[selected] == password:
                        if location.get("latitude") and location.get("longitude"):
                            lat = location['latitude']
                            long = location['longitude']
                            if (lat >= 18.08646 and lat <= 18.0999) and (long >= 83.37392 and long <= 83.3999):
                                st.session_state['user'] = selected  # Save the selection in session
                                # Device-bound check for attendance
                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute("SELECT device_id, mark_date, mark_time FROM attendance WHERE roll_number=?", (selected,))
                                row = cur.fetchone()
                                if row:
                                    bound_device_id, mark_date, mark_time = row
                                    if bound_device_id != device_id:
                                        st.error(f"ERROR: Roll number {selected} already marked as present by another device of id: {bound_device_id} on {mark_date}")
                                    else:
                                        st.warning(f"{selected} is already marked present (by this device).")
                                else:
                                    # Mark attendance
                                    cur.execute("INSERT INTO attendance (roll_number, device_id, mark_date, mark_time) VALUES (?, ?, ?, ?)", (selected, device_id, today, input_time))
                                    conn.commit()
                                    # Also update CSV for compatibility
                                    already_marked = attendance_df[(attendance_df['Name'] == selected) & (attendance_df['Date'] == today)]
                                    if already_marked.empty:
                                        data = [[st.session_state['session_id'], selected, today]]
                                        new_df = pd.DataFrame(data, columns=['SessionID', 'Name', 'Date'])
                                        attendance_df = pd.concat([attendance_df, new_df], ignore_index=True)
                                        attendance_df.to_csv(ATTENDANCE_FILE, index=False)
                                    st.success(f"You ({selected}) are now marked as present for {today}!")
                            else:
                                st.error("Your Location is not matching i.e you aren't there in college!!")
                        else:
                            st.error("Didn't fetch Location, try providing location once more!!")
                    else:
                        st.error('WRONG PASSWORD!!')
                else:
                    # Session has already a user who marked attendance 
                    if st.session_state['user'] != selected:
                        st.error(f"This device/browser is already used by {st.session_state['user']}. You cannot mark for others during this session!")
                    else:
                        st.warning(f"{selected} has already marked attendance for this session.")
            if st.session_state['user'] is not None:
                if st.button("Change User"):
                    # (1) Remove the last attendance row for this session, if marked
                    today = datetime.today().strftime('%Y-%m-%d')
                    mask = ~((attendance_df['SessionID'] == st.session_state['session_id']) & (attendance_df['Date'] == today))
                    attendance_df = attendance_df[mask]
                    attendance_df.to_csv(ATTENDANCE_FILE, index=False)
                    
                    # (2) Clear session state and assign a new session ID
                    st.session_state['user'] = None
                    st.session_state['session_id'] = get_session_id()
                    st.success("Session released! You can select a new user and try again.")

        elif role == 'Class Representative':
            rep_pass = st.text_input("Enter Rep Password:", type='password')
            selected_date = st.date_input("Select Date to View Attendance:", value=datetime.today())
            selected_date_str = selected_date.strftime('%Y-%m-%d')

            if st.button('View Attendance'):
                if rep_pass == rep_password:
                    daily_attendance = attendance_df[attendance_df['Date'] == selected_date_str]
                    present_list = daily_attendance['Name'].tolist()
                    absent_list = [name for name in options if name not in present_list]

                    st.subheader(f'Attendance for {selected_date_str}:')
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        cola, colb = st.columns(2)
                        with cola:
                            st.write('**Presenties:**')
                            if present_list:
                                for name in present_list:
                                    st.write(f"- {name}")
                            else:
                                st.write("No one present.")
                        with colb:
                            st.write('**Absenties:**')
                            if absent_list:
                                for name in absent_list:
                                    st.write(f"- {name}")
                            else:
                                st.write("Everyone present!")
                else:
                    st.error('Wrong Rep Password!')

            if st.button('Reset Attendance for Selected Date') and rep_pass == rep_password:
                attendance_df = attendance_df[attendance_df['Date'] != selected_date_str]
                attendance_df.to_csv(ATTENDANCE_FILE, index=False)
                st.info(f"Attendance reset for {selected_date_str}!")

#======================= Chat Arrangement ======================== 
st.markdown("""
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">

<style>
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 20px;
    max-width: 100%;
    width: 100%;
}

.chat-bubble {
    padding: 10px 15px;
    border-radius: 15px;
    max-width: 70%;
    word-wrap: break-word;
    font-size: 16px;
    display: block;  /* Changed to block for better stacking */
}

.left-bubble {
    align-self: flex-start;
    background-color: #dcf8c6; /* light green */
    margin-bottom: 10px;
    margin-top: 10px;
    color: black;
    border-top-left-radius: 0;
    text-align: left;
}

.right-bubble {
    align-self: flex-end;
    margin-bottom: 10px;
    margin-top: 10px;
    background-color: #add8e6; /* light blue */
    color: black;
    border-top-right-radius: 0;
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

with tab3:
    # Security check: Ensure roll_no is entered and bound to this device
    if not Roll_no or not check_device_binding(Roll_no):
        st.error("Please register first and ensure your roll number is bound to this device.")
    else:
        MESSAGE_FILE = "messages.csv"
        if not os.path.exists(MESSAGE_FILE):
            message_df = pd.DataFrame(columns=['Roll_no', 'Message'])
            message_df.to_csv(MESSAGE_FILE, index=False)
        else:
            message_df = pd.read_csv(MESSAGE_FILE)  
        issue = st.chat_input("Enter your issue: ")
        if Roll_no != "" and Roll_no in options:
            if issue:
                new_msg = pd.DataFrame({"Roll_no":[Roll_no],"Message":[issue]})
                message_df = pd.concat([message_df,new_msg], ignore_index=True) 
                message_df.to_csv(MESSAGE_FILE) 
        else:
            st.error("!Enter NAME and ROLL NUMBER first!")  
        for idx,row in message_df.iterrows():
            chat_html = "<div class='chat-container'>"
            if row['Roll_no'] == Roll_no:
                chat_html += f"<div class='chat-bubble left-bubble'><b>{row['Roll_no']}</b>:{row['Message']}</div>"
            else:
                chat_html += f"<div class='chat-bubble right-bubble'><b>{row['Roll_no']}</b>:{row['Message']}</div>"
            chat_html += "</div>"
            st.markdown(chat_html, unsafe_allow_html=True)

        if st.button("Reset"):
            message_df = pd.DataFrame(columns=message_df.columns)
            message_df.to_csv(MESSAGE_FILE, index=False)
        if st.button("REFRESH"):
            st.rerun()

st.caption(f"Device ID: {device_id}")
