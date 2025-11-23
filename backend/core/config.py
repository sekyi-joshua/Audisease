import os

# Simple config module; extend as needed.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(BASE_DIR, "backend", "models")

MODEL_PATH = os.path.join(MODEL_DIR, "model.h5")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
