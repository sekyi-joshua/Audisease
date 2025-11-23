import io
import librosa
import numpy as np

from backend.ml.model_loader import model, scaler
from backend.ml.features import extract_features_from_signal, SAMPLE_RATE


def predict_audio_bytes(audio_bytes: bytes):
    """High-level prediction function used by API layer.

    Takes raw audio bytes, returns PD probability and friendly payload.
    """
    y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None, mono=True)
    if sr != SAMPLE_RATE:
        y = librosa.resample(y, orig_sr=sr, target_sr=SAMPLE_RATE)
        sr = SAMPLE_RATE

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
