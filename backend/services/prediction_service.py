import io
import platform
import librosa
import numpy as np
import soundfile as sf

from backend.ml.model_loader import model, scaler
from backend.ml.features import extract_features_from_signal, SAMPLE_RATE


def predict_audio_bytes(audio_bytes: bytes):
    """High-level prediction function used by API layer.

    Takes raw audio bytes, returns PD probability and friendly payload.
    """
    print("Start load")
    # On macOS, librosa.load() with BytesIO can fail, so use soundfile as fallback
    is_macos = platform.system() == "Darwin"
    
    try:
        if is_macos:
            # Use soundfile on macOS for better compatibility
            y, sr = sf.read(io.BytesIO(audio_bytes))
            # Ensure mono (average channels if stereo)
            if y.ndim > 1:
                y = y.mean(axis=1)
        else:
            # Try librosa on other platforms
            y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None, mono=True)
    except Exception as e:
        # Fallback to soundfile if librosa fails
        print(f"librosa.load failed ({e}), falling back to soundfile")
        y, sr = sf.read(io.BytesIO(audio_bytes))
        if y.ndim > 1:
            y = y.mean(axis=1)
    if sr != SAMPLE_RATE:
        print("resample")
        y = librosa.resample(y, orig_sr=sr, target_sr=SAMPLE_RATE)
        sr = SAMPLE_RATE

    print("Get feats")
    feats = extract_features_from_signal(y, sr)
    feats_scaled = scaler.transform(feats.reshape(1, -1))

    prob = float(model.predict(feats_scaled)[0][0])
    pct = round(prob * 100, 2)

    return {
        "probability": prob,
        "percentage": pct,
        "classification": "parkinsons_likely" if prob >= 0.5 else "parkinsons_unlikely",
        "disclaimer": "This is a research screening tool and not a medical diagnosis."
    }
