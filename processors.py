from streamlit_webrtc import VideoProcessorBase
import av
import cv2
from face_utils import recognize_face_from_frame

# ------------------ Enrollment Processor ------------------

class EnrollProcessor(VideoProcessorBase):
    """
    A video processor for capturing a frame from the webcam stream for face enrollment.
    """
    def __init__(self):
        self.latest_frame = None           # Most recent frame from webcam
        self.capture_requested = False     # Flag to trigger capture
        self.captured_frame = None         # Captured image

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        """
        Processes each incoming frame.

        If capture is requested, saves a copy of the current frame.

        Args:
            frame (av.VideoFrame): Input video frame

        Returns:
            av.VideoFrame: Output frame to display
        """
        img = frame.to_ndarray(format="bgr24")
        self.latest_frame = img

        if self.capture_requested:
            self.captured_frame = img.copy()
            self.capture_requested = False  # Reset after capture

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ------------------ Recognition Processor ------------------

class RecognitionProcessor(VideoProcessorBase):
    """
    A video processor that performs real-time face recognition on webcam frames.
    """
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        """
        Detects and identifies faces in the frame.

        Args:
            frame (av.VideoFrame): Input video frame

        Returns:
            av.VideoFrame: Annotated frame with bounding boxes and labels
        """
        img = frame.to_ndarray(format="bgr24")
        results = recognize_face_from_frame(img)

        for (bbox, name, dist) in results:
            x1, y1, x2, y2 = map(int, bbox)
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            label = f"{name} ({dist:.2f})" if name != "Unknown" else "Unknown"

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")
