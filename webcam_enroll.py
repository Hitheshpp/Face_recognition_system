import os
import faiss
import pickle
import numpy as np
from insightface.app import FaceAnalysis
from mongo_utils import upload_file_to_gridfs

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_PATH = os.path.join(DATA_DIR, "index.faiss")
META_PATH = os.path.join(DATA_DIR, "metadata.pkl")

# Controls whether to sync with MongoDB GridFS
AUTO_UPLOAD = True

# Initialize InsightFace model (ArcFace)
model = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
model.prepare(ctx_id=0)

def load_or_create_faiss_index():
    """Load existing FAISS index or create a new one if not present."""
    if os.path.exists(INDEX_PATH) and os.path.getsize(INDEX_PATH) > 0:
        try:
            return faiss.read_index(INDEX_PATH)
        except Exception:
            pass
    index = faiss.IndexFlatL2(512)
    faiss.write_index(index, INDEX_PATH)
    return index

def load_or_create_metadata():
    """Load existing metadata or create a new list."""
    if os.path.exists(META_PATH) and os.path.getsize(META_PATH) > 0:
        try:
            with open(META_PATH, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    with open(META_PATH, "wb") as f:
        pickle.dump([], f)
    return []

# Load index and metadata on startup
index = load_or_create_faiss_index()
metadata = load_or_create_metadata()

def process_and_enroll(frame, name):
    """
    Detects face, computes embedding, and enrolls it with the given name.

    Args:
        frame (np.ndarray): Captured image from webcam.
        name (str): Person’s name to associate with the embedding.

    Returns:
        bool: True if enrollment successful, False otherwise.
    """
    faces = model.get(frame)
    if not faces:
        return False

    emb = faces[0].embedding
    emb = emb / np.linalg.norm(emb)

    index.add(np.expand_dims(emb.astype(np.float32), axis=0))
    metadata.append(name)

    # Save locally
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)

    # Sync with MongoDB GridFS
    if AUTO_UPLOAD:
        upload_file_to_gridfs(INDEX_PATH, "index.faiss")
        upload_file_to_gridfs(META_PATH, "metadata.pkl")

    return True
