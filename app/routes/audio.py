# API Endpoints for Fingerprinting
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.audio import Audio
from app.services.storage import save_temp_file, save_permanent_file
from app.services.match import run_fingerprint_check
from typing import List, Dict
import os
from datetime import datetime

router = APIRouter(prefix="/audio", tags=["audio"])

@router.post("/upload", response_model=Audio)
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload an audio file to the reference library.
    """
    try:
        # Save file permanently and generate fingerprint
        file_path = save_permanent_file(file)
        
        # Get file information
        file_info = os.stat(file_path)
        
        # Construct Audio object
        audio = Audio(
            id=1,  # This would come from a database in a real implementation
            filename=os.path.basename(file_path),
            file_type=file.content_type,
            size=file_info.st_size,
            created_at=datetime.fromtimestamp(file_info.st_ctime),
            file_path=file_path
        )
        
        return audio
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/match")
async def match_audio(file: UploadFile = File(...)):
    """
    Check if uploaded audio matches any reference tracks.
    Returns matches and count.
    """
    try:
        # Save temporary file for analysis
        temp_path, cleanup = save_temp_file(file)
        
        try:
            # Run fingerprint check
            matches = run_fingerprint_check(temp_path)
            return {
                "matches": matches,
                "count": len(matches)
            }
        finally:
            # Clean up temporary file
            cleanup()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))