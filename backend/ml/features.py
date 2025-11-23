import numpy as np
import librosa

SAMPLE_RATE = 16000
N_MFCC = 20


def extract_features_from_signal(y: np.ndarray, sr: int):
    """Convert mono audio signal into a fixed-size numeric feature vector."""
    if y.size == 0:
        raise ValueError("Empty audio signal")

    # Normalize loudness
    y = librosa.util.normalize(y)

    # MFCCs
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    mfcc_mean = mfcc.mean(axis=1)
    mfcc_std = mfcc.std(axis=1)

    # Delta MFCCs
    mfcc_delta = librosa.feature.delta(mfcc)
    mfcc_delta_mean = mfcc_delta.mean(axis=1)
    mfcc_delta_std = mfcc_delta.std(axis=1)

    # Spectral features
    zcr = librosa.feature.zero_crossing_rate(y).mean()
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr).mean()
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr).mean()

    # RMS energy
    rms = librosa.feature.rms(y=y)
    rms_mean = rms.mean()
    rms_std = rms.std()

    features = np.hstack(
        [
            mfcc_mean,
            mfcc_std,
            mfcc_delta_mean,
            mfcc_delta_std,
            [zcr, centroid, bandwidth, rolloff],
            [rms_mean, rms_std],
        ]
    )

    return features.astype(np.float32)
