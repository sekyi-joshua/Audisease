from tensorflow import keras
from joblib import load
from backend.core.config import MODEL_PATH, SCALER_PATH

# Load trained model and scaler at import time for reuse across requests.
try:
    model = keras.models.load_model(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Unable to load model from {MODEL_PATH}: {e}")

try:
    scaler = load(SCALER_PATH)
except Exception as e:
    raise RuntimeError(f"Unable to load scaler from {SCALER_PATH}: {e}")
