# Fingerprint hashing
# Takes a user uploaded audio file and hashes it into a unique fingerprint
import hashlib


def hash_audio(file_path: str) -> str:
    # Generate a hash of the file content for naming scheme; fingerprint it
    with open(file_path, 'rb') as f:
        content = f.read()
        return hashlib.sha256(content).hexdigest()
