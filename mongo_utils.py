from pymongo import MongoClient
import gridfs
import streamlit as st
import datetime
import os

MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["face_recognition"]
fs = gridfs.GridFS(db, collection="faiss_data")

def upload_file_to_gridfs(local_path, mongo_filename):
    """
    Uploads a file to MongoDB GridFS under 'faiss_data' collection.
    Replaces existing file with the same name.

    Args:
        local_path (str): Local path to the file to upload.
        mongo_filename (str): The name to use in MongoDB GridFS.
    """
    try:
        if fs.exists({"filename": mongo_filename}):
            fs.delete(fs.get_last_version(filename=mongo_filename)._id)

        with open(local_path, "rb") as f:
            fs.put(f, filename=mongo_filename)

        print(f"✅ Uploaded {mongo_filename} to MongoDB GridFS.")
    except Exception as e:
        print(f"❌ Upload failed for {mongo_filename}: {e}")

def download_file_from_gridfs(mongo_filename, local_path):
    """
    Downloads a file from MongoDB GridFS to a local path.

    Args:
        mongo_filename (str): The filename in GridFS.
        local_path (str): Path to save the file locally.
    """
    try:
        if fs.exists({"filename": mongo_filename}):
            data = fs.get_last_version(filename=mongo_filename).read()
            with open(local_path, "wb") as f:
                f.write(data)
            print(f"✅ Downloaded {mongo_filename} from MongoDB to {local_path}")
        else:
            print(f"❌ File {mongo_filename} does not exist in MongoDB.")
    except Exception as e:
        print(f"❌ Download failed for {mongo_filename}: {e}")
