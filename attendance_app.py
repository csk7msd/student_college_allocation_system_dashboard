import streamlit as st
import qrcode
import pandas as pd
from urllib.parse import urlencode
import io
from geopy.distance import geodesic
import json

# --- Configuration ---
TARGET_LATITUDE = 18.88132
TARGET_LONGITUDE = 77.91965
ALLOWED_RADIUS_KM = 0.5

# Store data in session state for persistence
if "attendance_data" not in st.session_state:
    st.session_state.attendance_data = {}
if "attendance_sessions" not in st.session_state:
    st.session_state.attendance_sessions = {}
if "student_data" not in st.session_state:
    st.session_state.student_data = pd.DataFrame()

# --- Helper Functions ---
def generate_qr_code(session_id, base_url):
    """Generates a QR code URL with session data."""
    params = {'session_code': session_id}
    full_url = f"{base_url}?{urlencode(params)}"
    qr_img = qrcode.make(full_url)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    return buffer, full_url

def calculate_attendance_percentage(student_id):
    """Calculates the attendance percentage for a given student."""
    attended_sessions = len(st.session_state.attendance_data.get(student_id, []))
    total_sessions = len(st.session_state.attendance_sessions)
    if total_sessions == 0:
        return 0
    return (attended_sessions / total_sessions) * 100

def check_location(student_lat, student_lon):
    """Checks if the student's location is within the allowed radius."""
    target_location = (TARGET_LATITUDE, TARGET_LONGITUDE)
    student_location = (student_lat, student_lon)
    distance = geodesic(target_location, student_location).km
    return distance <= ALLOWED_RADIUS_KM, distance

# --- Streamlit UI ---
st.set_page_config(page_title="Attendance System", layout="wide")

url_params = st.query_params
session_code_from_url = url_params.get("session_code", [None])[0]

if session_code_from_url:
    # --- Student Page: Mark Attendance ---
    st.title("Student Attendance Portal")
    st.markdown("Please enter your details to mark attendance.")

    with st.form("attendance_form"):
        st.write(f"Session: **{st.session_state.attendance_sessions.get(session_code_from_url, 'Unknown Session')}**")
        name = st.text_input("Enter your Name")
        student_id = st.text_input("Enter your Student ID")
        
        st.session_state.qr_code_text = session_code_from_url
        
        submitted = st.form_submit_button("Mark Attendance")
    
    if submitted:
        if not st.session_state.student_data.empty:
            if str(student_id) not in st.session_state.student_data['ID'].astype(str).values:
                st.error("❌ Your Student ID is not in the student list.")
                st.stop()
            
        if not name or not student_id:
            st.warning("Please fill in both Name and Student ID.")
        else:
            st.info("Please allow location access. We are now checking your location.")
            
            st.write("For this demo, please provide your current location below.")
            lat = st.number_input("Enter your Latitude", format="%.5f")
            lon = st.number_input("Enter your Longitude", format="%.5f")
            
            if st.button("Submit Location"):
                if st.session_state.qr_code_text == session_code_from_url:
                    is_in_range, distance = check_location(lat, lon)
                    if is_in_range:
                        if student_id not in st.session_state.attendance_data:
                            st.session_state.attendance_data[student_id] = []
                        
                        if session_code_from_url not in st.session_state.attendance_data[student_id]:
                            st.session_state.attendance_data[student_id].append(session_code_from_url)
                            st.success(f"✅ Attendance marked for {name} ({student_id})!")
                        else:
                            st.info("You have already marked attendance for this session.")

                        attendance_percent = calculate_attendance_percentage(student_id)
                        st.metric("Your Attendance Percentage", f"{attendance_percent:.2f}%")
                        
                    else:
                        st.error(f"❌ Your location is too far. Distance: {distance:.2f} km.")
                else:
                    st.error("❌ Invalid QR code or session. Please scan a valid QR code.")

else:
    # --- Teacher Page: Generate QR Code ---
    st.title("QR Code Generator (Teacher Portal)")
    st.markdown("Generate a QR code for a new attendance session.")

    uploaded_file = st.file_uploader("Upload Student List CSV", type=["csv"], help="A CSV file with a column named 'ID' for student IDs.")
    if uploaded_file is not None:
        try:
            st.session_state.student_data = pd.read_csv(uploaded_file)
            st.success("Student list uploaded successfully!")
            st.dataframe(st.session_state.student_data.head())
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
            st.session_state.student_data = pd.DataFrame()

    if not st.session_state.student_data.empty:
        session_name = st.text_input("Enter Class/Session Name", "Introduction to Python")
        if st.button("Generate QR Code"):
            if session_name:
                session_id = f"session_{session_name.replace(' ', '_').lower()}_{len(st.session_state.attendance_sessions) + 1}"
                st.session_state.attendance_sessions[session_id] = session_name
                
                base_url = "http://localhost:8501"
                
                qr_image_buffer, full_url = generate_qr_code(session_id, base_url)
                
                st.subheader("Scan this QR code to mark attendance:")
                st.image(qr_image_buffer, caption=f"QR Code for {session_name}", width=300)
                
                # Download button for the generated QR code
                st.download_button(
                    label="Download QR Code as PNG",
                    data=qr_image_buffer,
                    file_name=f"{session_id}.png",
                    mime="image/png"
                )
                
                st.markdown(f"**URL:** `{full_url}`")
                st.info("Students can scan this code to be redirected to the attendance page.")
    else:
        st.warning("Please upload a student list CSV file to proceed.")

    st.markdown("---")
    st.subheader("Attendance Records")
    
    if st.session_state.attendance_data:
        records = []
        for student_id, sessions in st.session_state.attendance_data.items():
            if str(student_id) in st.session_state.student_data['ID'].astype(str).values:
                for session_id in sessions:
                    records.append({
                        "Student ID": student_id,
                        "Session Name": st.session_state.attendance_sessions.get(session_id, 'Unknown'),
                        "Percentage": f"{calculate_attendance_percentage(student_id):.2f}%"
                    })
        
        if records:
            df = pd.DataFrame(records)
            st.dataframe(df)
        else:
            st.info("No attendance records found for valid students.")
    else:
        st.info("No attendance records found.")
