# face_model.py

from insightface.app import FaceAnalysis

_model_instance = None

def get_face_model():
    global _model_instance
    if _model_instance is None:
        _model_instance = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        _model_instance.prepare(ctx_id=0)
    return _model_instance
