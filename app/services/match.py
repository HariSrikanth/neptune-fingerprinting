# Core Logic for Matching
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from app.services.storage import STORAGE_DIR
from app.services.fingerprint import generate_fingerprint
from app.services.storage import get_all_files, get_fingerprint
from app.services.hash import hash_audio
from app.services.sampling import SamplingMatch, analyze_sampling_pattern
import os
from functools import lru_cache
import logging
from collections import defaultdict

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cache for recently compared fingerprints
def get_cached_fingerprint(file_path: str) -> List[Tuple[int, int, int]]:
    """Get fingerprint with caching"""
    return generate_fingerprint(file_path)

def find_matches(input_fingerprint: List[Tuple[int, int, int]], 
                stored_fingerprint: List[Tuple[int, int, int]],
                threshold: float = 0.05) -> bool:
    """
    Check if two fingerprints match using Shazam-style time offset histogram.
    """
    if not input_fingerprint or not stored_fingerprint:
        return False
        
    # Quick check for exact match
    if input_fingerprint == stored_fingerprint:
        return True
    
    # Create hash lookup for stored fingerprint
    hash_lookup = defaultdict(list)
    for t1, t2, h in stored_fingerprint:
        hash_lookup[h].append((t1, t2))
    
    # Count time offsets between matching hashes
    offset_counts = defaultdict(int)
    total_matches = 0
    
    for t1, t2, h in input_fingerprint:
        if h in hash_lookup:
            # Found matching hash, check time alignment
            for stored_t1, stored_t2 in hash_lookup[h]:
                # Calculate time offset between input and stored
                offset = t1 - stored_t1
                offset_counts[offset] += 1
                total_matches += 1
    
    if not total_matches:
        return False
    
    # Find the most common time offset
    max_offset_count = max(offset_counts.values()) if offset_counts else 0
    alignment_ratio = max_offset_count / len(input_fingerprint)
    
    # Calculate overall match confidence
    match_ratio = total_matches / min(len(input_fingerprint), len(stored_fingerprint))
    
    # Combine alignment and match ratios
    confidence = (alignment_ratio * 0.6 + match_ratio * 0.4)
    
    return confidence >= threshold

def run_fingerprint_check(input_file_path: str) -> List[str]:
    """
    Check if input audio matches any stored audio.
    """
    # Generate fingerprint for input file
    input_fingerprint = generate_fingerprint(input_file_path)
    
    # Get all stored files
    stored_files = get_all_files()
    
    # Check for matches
    matches = []
    for stored_file in stored_files:
        stored_fingerprint = get_fingerprint(stored_file)
        if stored_fingerprint and find_matches(input_fingerprint, stored_fingerprint):
            matches.append(os.path.basename(stored_file))
    
    return matches