from typing import List, Tuple, Dict
import numpy as np
from dataclasses import dataclass
from enum import Enum

class MatchType(Enum):
    EXACT = "exact"  # Direct copy
    SAMPLED = "sampled"  # Modified sample
    REFERENCED = "referenced"  # Similar but not sampled

@dataclass
class SamplingMatch:
    original_track: str
    match_type: MatchType
    confidence: float
    time_offset: float  # Where in the original track the match was found
    duration: float  # How long the match is

def detect_sampling(input_fingerprint: List[Tuple[int, int, int]], 
                   original_fingerprint: List[Tuple[int, int, int]],
                   threshold: float = 0.7) -> Tuple[bool, float]:
    """
    Detect if input audio contains sampling from original audio.
    
    Args:
        input_fingerprint: Fingerprint of the input audio
        original_fingerprint: Fingerprint of the original audio
        threshold: Minimum confidence required for a match
        
    Returns:
        Tuple of (is_match, confidence)
    """
    # Quick check for exact match
    if input_fingerprint == original_fingerprint:
        return True, 1.0
        
    # Extract hash values and time information
    input_hashes = {(t1, t2, h) for t1, t2, h in input_fingerprint}
    original_hashes = {(t1, t2, h) for t1, t2, h in original_fingerprint}
    
    # Find matching hashes
    common_hashes = input_hashes.intersection(original_hashes)
    
    # Calculate match ratio
    match_ratio = len(common_hashes) / min(len(input_hashes), len(original_hashes))
    
    # Lower threshold for exact matches
    if match_ratio > 0.95:
        return True, match_ratio
    
    return match_ratio >= threshold, match_ratio

def analyze_sampling_pattern(input_fingerprint: List[Tuple[int, int, int]],
                           original_fingerprint: List[Tuple[int, int, int]],
                           original_track_id: str) -> SamplingMatch:
    """
    Analyze the sampling pattern to determine type and confidence.
    
    Args:
        input_fingerprint: Fingerprint of the input audio
        original_fingerprint: Fingerprint of the original audio
        original_track_id: ID of the original track
        
    Returns:
        SamplingMatch object with analysis results
    """
    is_match, confidence = detect_sampling(input_fingerprint, original_fingerprint)
    
    if not is_match:
        return None
    
    # Determine match type based on confidence and pattern
    if confidence > 0.95:
        match_type = MatchType.EXACT
    elif confidence > 0.7:
        match_type = MatchType.SAMPLED
    else:
        match_type = MatchType.REFERENCED
    
    # Calculate time offset and duration (simplified)
    time_offset = 0.0  # Would need more complex analysis
    duration = 5.0  # Default segment duration
    
    return SamplingMatch(
        original_track=original_track_id,
        match_type=match_type,
        confidence=confidence,
        time_offset=time_offset,
        duration=duration
    ) 