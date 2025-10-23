import streamlit as st
import cv2
from deepface import DeepFace
import pandas as pd
import os

st.title("Attendance Face Verification System")

def save_face_image(img_path):
    cam = cv2.VideoCapture(0)
    st.info("Press space to capture your image.")
    while True:
        ret, frame = cam.read()
        cv2.imshow("Capture Your Face", frame)
        if cv2.waitKey(1) & 0xFF == ord(' '):
            cv2.imwrite(img_path, frame)
            st.success(f"Image saved as {img_path}")
            break
    cam.release()
    cv2.destroyAllWindows()

# Attendance DataFrame management
data_file = 'attendance.csv'
if os.path.exists(data_file):
    attendance = pd.read_csv(data_file)
else:
    attendance = pd.DataFrame(columns=["Name", "Roll No", "Present"])

mode = st.radio("Are you Registering for the first time or Marking Attendance?",
                ("Register", "Mark Present"))

name = st.text_input("Enter Name")
roll_no = st.text_input("Enter Roll No")
ref_img_path = f"ref_{roll_no}.jpg"

if mode == "Register":
    if st.button("Register & Capture Reference Image"):
        if not os.path.exists(ref_img_path):
            save_face_image(ref_img_path)
            # Store record if registering for first time
            if attendance[attendance['Roll No'] == roll_no].empty:
                attendance = pd.concat([attendance,pd.DataFrame({"Name": [name], "Roll No": [roll_no], "Present": [False]})], ignore_index=True)
                attendance.to_csv(data_file, index=False)
        else:
            st.warning("Reference image already exists for this Roll No! Registration can only be done once.")

elif mode == "Mark Present":
    if st.button("Mark Present"):
        # Check if registered
        if os.path.exists(ref_img_path):
            test_img_path = f"test_present_{roll_no}.jpg"
            save_face_image(test_img_path)
            # Run DeepFace verification
            result = DeepFace.verify(test_img_path, ref_img_path, enforce_detection=False)
            if result["verified"]:
                attendance.loc[attendance["Roll No"] == roll_no, "Present"] = True
                attendance.to_csv(data_file, index=False)
                st.success("You are marked PRESENT! ✅")
            else:
                st.error("Face Verification Failed. Not marked present.")
        else:
            st.error("No registration record found for this Roll No.")

# Optionally, show status
if name and roll_no:
    user = attendance[(attendance["Roll No"] == roll_no)]
    if not user.empty:
        st.info(f"Status: {'Present' if user.iloc[0]['Present'] else 'Absent'}")

#py -3.11 -m streamlit run fing.py