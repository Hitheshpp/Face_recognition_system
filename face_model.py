# face_model.py

from insightface.app import FaceAnalysis
import threading

_model_instance = None
_model_lock = threading.Lock()

def get_face_model():
    global _model_instance

    if _model_instance is None:
        with _model_lock:
            if _model_instance is None:  # Double-checked locking
                print("[INFO] Loading InsightFace model...")
                _model_instance = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
                _model_instance.prepare(ctx_id=0)
                print("[INFO] InsightFace model loaded.")
    
    return _model_instance
