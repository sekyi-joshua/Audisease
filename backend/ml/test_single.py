import numpy as np
import librosa
from joblib import load
import tensorflow as tf
from backend.ml.features import extract_features_from_signal, SAMPLE_RATE

# Paths to your saved model and scaler
MODEL_PATH = r"C:\Personal project\AuDisease\backend\models\model.h5"
SCALER_PATH = r"C:\Personal project\AuDisease\backend\models\scaler.pkl"

def load_model_and_scaler():
    model = tf.keras.models.load_model(MODEL_PATH)
    scaler = load(SCALER_PATH)
    return model, scaler

def predict_audio(path_to_wav):
    print(f"Loading your audio: {path_to_wav}")

    # Load your voice at the same sample rate used during training
    signal, sr = librosa.load(path_to_wav, sr=SAMPLE_RATE)

    # Extract MFCC + jitter + shimmer + HNR + spectral features
    features = extract_features_from_signal(signal, sr)
    features = np.array(features).reshape(1, -1)

    # Load scaler + model
    model, scaler = load_model_and_scaler()

    # Scale features
    features_scaled = scaler.transform(features)

    # Predict PD probability (sigmoid output)
    prob = model.predict(features_scaled)[0][0]

    print("\n===== RESULT =====")
    print(f"Parkinson’s Probability: {prob:.4f}")
    print(f"Prediction: {'PD' if prob >= 0.5 else 'Healthy'}")

    return prob

if __name__ == "__main__":
    # CHANGE THIS TO YOUR AUDIO FILE PATH
    your_audio = r"C:\Users\manin\Downloads\test\my_voice.wav"
    predict_audio(your_audio)
