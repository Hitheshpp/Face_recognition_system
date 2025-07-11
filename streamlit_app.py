# streamlit_app.py

import streamlit as st
from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer
from webcam_enroll import process_and_enroll
from face_utils import delete_enrolled_face
from processors import EnrollProcessor, RecognitionProcessor
from face_model import get_face_model
from insightface.app import FaceAnalysis
import os
os.environ["INSIGHTFACE_CACHE"] = "/tmp/insightface_cache"
# --------- Cache the model so it loads only once ---------
# @st.cache_resource
# def load_model():
#     model = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
#     model.prepare(ctx_id=0)
#     return model

def main():
    RTC_CONFIGURATION = RTCConfiguration(
        {
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]},
                {
                    "urls": ["turn:openrelay.metered.ca:80"],
                    "username": "openrelayproject",
                    "credential": "openrelayproject"
                }
            ]
        }
    )

    # Page configuration
    st.set_page_config(page_title="Face Recognition System")
    st.title("🧠 Face Recognition System")

    # ---------- Load Face Model ----------
    model = get_face_model()

    # ---------- Session State Initialization ----------
    for key in ['captured', 'camera_started', 'recognition_started', 'frame', 'enroll_active', 'recognize_active', 'name']:
        if key not in st.session_state:
            st.session_state[key] = False if key != 'frame' else None

    # ---------- Face Enrollment Section ----------
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
                processor.capture_requested = True
                st.toast("📷 Capturing...")

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
        def enroll_processor_factory():
            return EnrollProcessor(model)

        ctx = webrtc_streamer(
            key="enroll_stream",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIGURATION,
            video_processor_factory=enroll_processor_factory,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True
        )

        if ctx.video_processor:
            st.session_state.enroll_processor = ctx.video_processor

    # Spacer
    st.markdown("<div style='margin-top: 60px'></div>", unsafe_allow_html=True)

    # ---------- Face Recognition Section ----------
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

    if st.session_state.recognition_started:
        def recognition_processor_factory():
            return RecognitionProcessor(model)

        webrtc_streamer(
            key="recognition_stream",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIGURATION,
            video_processor_factory=recognition_processor_factory,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    # Spacer
    st.markdown("<div style='margin-top: 60px'></div>", unsafe_allow_html=True)

    # ---------- Face Deletion Section ----------
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

if __name__ == "__main__":
    main()
