import os
import pickle
import numpy as np
import faiss
import insightface
from face_mode import get_face_model    
from webcam_enroll import INDEX_PATH, META_PATH
from mongo_utils import upload_file_to_gridfs, download_file_from_gridfs

# Initialize InsightFace model (ArcFace)
#model = insightface.app.FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
model = get_face_model()
model.prepare(ctx_id=0)

# Global variables for index and metadata
index = None
metadata = None
last_index_mtime = None
last_meta_mtime = None

RECOGNITION_THRESHOLD = 1.5  # Distance threshold for face recognition


def reload_index_and_metadata():
    """Reloads the FAISS index and metadata from disk."""
    try:
        if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
            return None, None

        index = faiss.read_index(INDEX_PATH)

        with open(META_PATH, "rb") as f:
            metadata = pickle.load(f)

        if not isinstance(metadata, list) or len(metadata) != index.ntotal:
            return None, None

        return index, metadata

    except Exception:
        return None, None


def recognize_face_from_frame(frame):
    """
    Recognizes faces in a given frame using FAISS index and metadata.

    Args:
        frame (np.ndarray): Frame from webcam.

    Returns:
        list: List of tuples (bounding_box, name, distance).
    """
    global index, metadata, last_index_mtime, last_meta_mtime

    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        return []

    # Reload index if modified or not loaded
    current_index_mtime = os.path.getmtime(INDEX_PATH)
    current_meta_mtime = os.path.getmtime(META_PATH)

    if (index is None or metadata is None or
        last_index_mtime != current_index_mtime or
        last_meta_mtime != current_meta_mtime):

        download_file_from_gridfs("index.faiss", INDEX_PATH)
        download_file_from_gridfs("metadata.pkl", META_PATH)
        index, metadata = reload_index_and_metadata()
        last_index_mtime = current_index_mtime
        last_meta_mtime = current_meta_mtime

    faces = model.get(frame)
    results = []

    for face in faces:
        emb = face.embedding / np.linalg.norm(face.embedding)
        distances, indices = index.search(np.expand_dims(emb, axis=0), k=1)
        dist = distances[0][0]
        idx = indices[0][0]
        name = metadata[idx] if dist < RECOGNITION_THRESHOLD else "Unknown"
        results.append((face.bbox, name, dist))

    return results


def delete_enrolled_face(name_to_delete):
    """
    Deletes a face and its embedding from the FAISS index and metadata.

    Args:
        name_to_delete (str): Name of the person to delete.

    Returns:
        bool: True if deletion successful, False otherwise.
    """
    global index, metadata, last_index_mtime, last_meta_mtime

    if metadata is None or index is None:
        return False

    indices_to_keep = [i for i, name in enumerate(metadata) if name != name_to_delete]
    if len(indices_to_keep) == len(metadata):
        return False  # No match found

    new_metadata = [metadata[i] for i in indices_to_keep]
    embeddings = index.reconstruct_n(0, index.ntotal)

    if not indices_to_keep:
        new_index = faiss.IndexFlatL2(512)  # Empty index
    else:
        new_embeddings = np.array([embeddings[i] for i in indices_to_keep], dtype=np.float32)
        new_index = faiss.IndexFlatL2(new_embeddings.shape[1])
        new_index.add(new_embeddings)

    metadata.clear()
    metadata.extend(new_metadata)
    index = new_index

    # Save and upload updated index/metadata
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)

    upload_file_to_gridfs(INDEX_PATH, "index.faiss")
    upload_file_to_gridfs(META_PATH, "metadata.pkl")

    # Re-download and reload
    download_file_from_gridfs("index.faiss", INDEX_PATH)
    download_file_from_gridfs("metadata.pkl", META_PATH)
    index, metadata = reload_index_and_metadata()

    if os.path.exists(INDEX_PATH):
        last_index_mtime = os.path.getmtime(INDEX_PATH)
    if os.path.exists(META_PATH):
        last_meta_mtime = os.path.getmtime(META_PATH)

    return index is not None and metadata is not None
