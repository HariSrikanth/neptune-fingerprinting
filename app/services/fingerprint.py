import numpy as np
import librosa
from typing import List, Tuple
from scipy.ndimage import maximum_filter
from scipy.ndimage import gaussian_filter

def find_peaks(spectrogram: np.ndarray, threshold: float = 0.3, 
              neighborhood_size: Tuple[int, int] = (30, 30)) -> List[Tuple[int, int]]:
    """
    Find peaks in the spectrogram using a local maximum filter.
    Uses Shazam-style peak finding with frequency-based thresholds.
    """
    # Apply local maximum filter
    data_max = maximum_filter(spectrogram, size=neighborhood_size)
    peak_mask = (spectrogram == data_max)
    
    # Apply frequency-dependent threshold
    freq_threshold = np.mean(spectrogram, axis=1) * threshold
    freq_threshold = freq_threshold[:, np.newaxis]
    peak_mask = peak_mask & (spectrogram > freq_threshold)
    
    # Get peak coordinates
    peaks = list(zip(*np.where(peak_mask)))
    
    # Sort peaks by amplitude for consistent processing
    peak_amplitudes = [spectrogram[i, j] for i, j in peaks]
    peaks = [x for _, x in sorted(zip(peak_amplitudes, peaks), reverse=True)]
    
    # Convert numpy types to Python native types
    peaks = [(int(i), int(j)) for i, j in peaks]
    
    return peaks

def generate_hashes(peaks: List[Tuple[int, int]], 
                   fan_out: int = 15,
                   target_zone_size: int = 5) -> List[Tuple[int, int, int]]:
    """
    Generate hashes from peaks using Shazam's target zone approach.
    """
    if not peaks:
        return []
        
    hashes = []
    for i, anchor in enumerate(peaks[:-1]):
        # Define target zone
        freq_anchor, time_anchor = anchor
        
        # Look at the next fan_out peaks in the target zone
        for j in range(1, min(fan_out, len(peaks) - i)):
            freq_target, time_target = peaks[i + j]
            
            # Skip if time difference is too large
            time_delta = time_target - time_anchor
            if time_delta <= 0 or time_delta > target_zone_size * 2:
                continue
                
            # Create hash using both frequency and time information
            hash_str = f"{freq_anchor}|{freq_target}|{time_delta}"
            hash_value = hash(hash_str) & 0xFFFFFFFF  # 32-bit hash
            
            # Ensure all values are Python native types
            hashes.append((int(time_anchor), int(time_target), int(hash_value)))
    
    return sorted(hashes)

def generate_fingerprint(audio_path: str) -> List[Tuple[int, int, int]]:
    """
    Generate a fingerprint for an audio file using spectral analysis.
    Uses Shazam-style constellation mapping.
    """
    # Load and preprocess audio
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Apply pre-emphasis to boost high frequencies
    y = librosa.effects.preemphasis(y)
    
    # Generate spectrogram with parameters optimized for speech
    S = librosa.stft(y, n_fft=2048, hop_length=512, window='hann')
    S = np.abs(S) ** 2
    
    # Convert to log scale and normalize
    S = librosa.power_to_db(S, ref=np.max)
    S = (S - S.min()) / (S.max() - S.min())
    
    # Apply slight smoothing
    S = gaussian_filter(S, sigma=1)
    
    # Find peaks (constellation points)
    peaks = find_peaks(S)
    
    # Generate hashes from peaks
    hashes = generate_hashes(peaks)
    
    return hashes 