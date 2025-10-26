import streamlit as st
import pandas as pd
import hashlib, uuid, os
from streamlit_cookies_controller import CookieController

#================= Persistent Device ID using Cookies =================
controller = CookieController()

# ensure cookies fully load
if not controller.getAll():
    st.write("")

if controller.get("device_id"):
    device_id = controller.get("device_id")
else:
    new_id = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
    controller.set("device_id", new_id, max_age=3600 * 24 * 365)  # valid for 1 year
    device_id = new_id

st.session_state["device_id"] = device_id
#======================================================================

MARKED_FILE = "marked.csv"
if not os.path.exists(MARKED_FILE):
    pd.DataFrame(columns=["Roll_no", "device_id"]).to_csv(MARKED_FILE, index=False)

marked_df = pd.read_csv(MARKED_FILE)

#================= Application UI =================
st.title("Register / Login")

registered_entry = marked_df.loc[marked_df["device_id"] == device_id]

# If this device already registered
if not registered_entry.empty:
    saved_roll = registered_entry.iloc[0]["Roll_no"]
    st.success(f"You are permanently registered with Roll No: {saved_roll}")
    st.text_input("Roll Number", value=saved_roll, disabled=True)
    st.info("You cannot change Roll Number on this device.")
    st.caption(f"Device ID: {device_id}")

# If not yet registered
else:
    name = st.text_input("Enter your Name:")
    roll_no = st.text_input("Enter your Roll Number:")
    if st.button("Register"):
        if not name or not roll_no:
            st.error("Please fill in all fields.")
        else:
            # Prevent using same Roll_no on another device
            if roll_no in marked_df["Roll_no"].values:
                st.error("This Roll Number is already bound to another device!")
            else:
                new_row = pd.DataFrame([{"Roll_no": roll_no, "device_id": device_id}])
                marked_df = pd.concat([marked_df, new_row], ignore_index=True)
                marked_df.to_csv(MARKED_FILE, index=False)
                st.success(f"Registered successfully as {roll_no}")
                st.rerun()
