# streamlit_app.py

import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import cv2
import numpy as np
from webcam_enroll import process_and_enroll
from processors import EnrollProcessor, RecognitionProcessor
from face_utils import delete_enrolled_face, recognize_face_from_frame
from styling import set_blurred_background, css_2


#---------------Page configuration-----------------------------------------
st.set_page_config(page_title="Face Recognition System")

st.title("🧠 Face Recognition System")

#------------Background image with blur------------------------------------

set_blurred_background("background.jpg")

st.markdown(css_2,unsafe_allow_html=True)

# ---------- Session State Initialization ----------------------------------

for key in ['captured', 'camera_started', 'recognition_started', 'frame', 'enroll_active', 'recognize_active', 'name']:
    if key not in st.session_state:
        st.session_state[key] = False if key != 'frame' else None

# ---------- Face Enrollment Section ----------------------------------------

st.subheader("📝 Face Enrollment")
st.session_state.name = st.text_input("Enter your name for enrollment")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📷 Start Camera", key="start_camera"):
        if st.session_state.name.strip() == "":
            st.warning("⚠️ Please enter a name before starting the camera.")
        else:
            st.session_state.camera_started = True
            st.session_state.enroll_active = True
            st.session_state.captured = False

with col2:
    if st.button("✅ Capture Face", key="capture_face"):
        processor = st.session_state.get("enroll_processor", None)

        if processor:
            # Request capture from processor
            processor.capture_requested = True
            st.toast("📷 Capturing...")

            # Wait briefly to ensure capture happens
            import time
            time.sleep(0.5)

            frame = processor.captured_frame

            if frame is not None:
                success = process_and_enroll(frame, st.session_state.name)
                if success:
                    st.success(f"✅ Enrolled: {st.session_state.name}")
                    st.session_state.camera_started = False
                    st.session_state.enroll_active = False
                    st.session_state.captured = True
                else:
                    st.warning("😕 Face not detected. Try again.")
            else:
                st.warning("❌ Frame not captured. Try again.")

with col3:
    if st.button("⏹️ Stop Camera", key="stop_camera"):
        st.session_state.camera_started = False
        st.session_state.enroll_active = False
        st.session_state.captured = False
        st.session_state.frame = None

# Webcam Stream for Enrollment
if st.session_state.get("camera_started") and st.session_state.get("enroll_active") and not st.session_state.get("captured"):
    ctx = webrtc_streamer(
        key="enroll_stream",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=EnrollProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if ctx.video_processor:
        st.session_state.enroll_processor = ctx.video_processor

# Spacer
st.markdown("<div style='margin-top: 60px'></div>", unsafe_allow_html=True)

# ---------- Face Recognition Section ------------------------------------------
st.subheader("🔍 Real-Time Face Recognition")

col4, col5 = st.columns(2)

with col4:
    if st.button("▶️ Start Recognition", key="start_recog"):
        st.session_state.recognition_started = True
        st.session_state.recognize_active = True

with col5:
    if st.button("⏹️ Stop Recognition", key="stop_recog"):
        st.session_state.recognition_started = False
        st.session_state.recognize_active = False

# Webcam Stream for Recognition
if st.session_state.recognition_started:
    webrtc_streamer(
        key="recognition_stream",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=RecognitionProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

# ---------- Face Recognition from Uploaded Image ---------------------------------

st.markdown("<div style='margin-top: 60px'></div>", unsafe_allow_html=True)
st.subheader("📤 Upload Image & Recognize Face")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    uploaded_image = cv2.imdecode(file_bytes, 1)

    st.image(uploaded_image, caption="Uploaded Image", channels="BGR")

    if st.button("🔍 Detect & Display"):
        results = recognize_face_from_frame(uploaded_image)

        for (bbox, name, dist) in results:
            x1, y1, x2, y2 = [int(v) for v in bbox]
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            label = f"{name} ({dist:.2f})" if name != "Unknown" else "Unknown"

            cv2.rectangle(uploaded_image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(uploaded_image, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        st.image(uploaded_image, caption="Recognition Result", channels="BGR")

# Spacer
st.markdown("<div style='margin-top: 60px'></div>", unsafe_allow_html=True)

# ---------- Face Deletion Section ------------------------------------------------

st.subheader("🗑️ Delete Enrolled Face")

delete_name = st.text_input("Enter the name to delete")

if st.button("❌ Delete Face"):
    if delete_name.strip() == "":
        st.warning("⚠️ Please enter a name.")
    else:
        success = delete_enrolled_face(delete_name.strip())
        if success:
            st.success(f"✅ Deleted face data for: {delete_name}")
        else:
            st.error(f"❌ Could not find face data for: {delete_name}")


#---------------------------------END----------------------------------------------#