# Helpers for Storage / Interfacing with IPFS

import os
import tempfile
import hashlib
from fastapi import UploadFile, HTTPException
from pathlib import Path
import pydub
from pydub import AudioSegment
from app.services.hash import hash_audio
from typing import Tuple, Callable, List, Any
import json
from app.services.fingerprint import generate_fingerprint
import numpy as np

# Create storage directories
STORAGE_DIR = Path("audio_storage")
TEMP_DIR = Path("temp_storage")
FINGERPRINT_DIR = Path("fingerprint_storage")

# Ensure directories exist
STORAGE_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
FINGERPRINT_DIR.mkdir(exist_ok=True)

# Supported audio formats
SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}

# JSON encoder that handles numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def cleanup_temp_files(file_paths: List[str]) -> None:
    """
    Clean up temporary files.
    
    Args:
        file_paths: List of file paths to clean up
    """
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

def convert_to_wav(input_path: str) -> str:
    """Convert any supported audio format to WAV"""
    # Get file extension
    ext = os.path.splitext(input_path)[1].lower()
    
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported audio format: {ext}")
    
    # If already WAV, just return the path
    if ext == '.wav':
        return input_path
    
    # Load audio file
    audio = AudioSegment.from_file(input_path, format=ext[1:])
    
    # Convert to WAV
    wav_path = str(TEMP_DIR / f"{os.path.basename(input_path)}.wav")
    audio.export(wav_path, format="wav")
    
    return wav_path

def save_temp_file(file: UploadFile) -> Tuple[str, Callable[[], None]]:
    """
    Save a temporary file and return its path and cleanup function.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        Tuple of (wav_file_path, cleanup_function)
    """
    # Save uploaded file
    temp_path = str(TEMP_DIR / file.filename)
    with open(temp_path, "wb") as f:
        content = file.file.read()
        f.write(content)
    
    # Convert to WAV if needed
    wav_path = convert_to_wav(temp_path)
    
    # Create list of files to clean up
    files_to_cleanup = [temp_path]
    if wav_path != temp_path:
        files_to_cleanup.append(wav_path)
    
    def cleanup():
        cleanup_temp_files(files_to_cleanup)
    
    return wav_path, cleanup

def save_permanent_file(file: UploadFile) -> str:
    """
    Save a file permanently with its fingerprint.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        Path to the saved file
    """
    # Save and convert to WAV
    wav_path, cleanup = save_temp_file(file)
    
    try:
        # Generate fingerprint
        fingerprint = generate_fingerprint(wav_path)
        
        # Generate hash for filename
        file_hash = hash_audio(wav_path)
        saved_path = STORAGE_DIR / f"{file_hash}.wav"
        
        # Copy the file instead of renaming to avoid cross-device link errors
        with open(wav_path, 'rb') as src:
            with open(saved_path, 'wb') as dst:
                dst.write(src.read())
        
        # Save fingerprint
        fingerprint_path = FINGERPRINT_DIR / f"{file_hash}.json"
        with open(fingerprint_path, 'w') as f:
            json.dump(fingerprint, f, cls=NumpyEncoder)
        
        return str(saved_path)
    finally:
        cleanup()

def get_all_files() -> List[str]:
    """Get all stored files"""
    return [str(f) for f in STORAGE_DIR.glob("*.*")]

def get_fingerprint(file_path: str) -> List[Tuple[int, int, int]]:
    """
    Get the fingerprint for a stored file.
    
    Args:
        file_path: Path to the stored file
        
    Returns:
        List of (t1, t2, hash) tuples representing the fingerprint
    """
    file_hash = os.path.splitext(os.path.basename(file_path))[0]
    fingerprint_path = FINGERPRINT_DIR / f"{file_hash}.json"
    
    if not fingerprint_path.exists():
        return None
    
    with open(fingerprint_path, 'r') as f:
        return json.load(f)