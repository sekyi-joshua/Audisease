import os
import argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
from joblib import dump
from tensorflow import keras
from tensorflow.keras import layers

from backend.ml.features import extract_features_from_signal, SAMPLE_RATE
from backend.core.config import MODEL_DIR, MODEL_PATH, SCALER_PATH
import librosa


def build_pd_model(input_dim: int):
    """Simple feed-forward binary classifier for Parkinson's vs healthy."""
    l2 = keras.regularizers.l2(1e-4)

    inp = keras.Input(shape=(input_dim,))
    x = layers.Dense(128, activation="relu", kernel_regularizer=l2)(inp)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(64, activation="relu", kernel_regularizer=l2)(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(32, activation="relu", kernel_regularizer=l2)(x)
    out = layers.Dense(1, activation="sigmoid")(x)

    model = keras.Model(inputs=inp, outputs=out, name="pd_voice_model")

    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="binary_crossentropy",
        metrics=["accuracy", keras.metrics.AUC(name="auc")],
    )
    return model


def load_dataset(metadata_path: str, base_dir: str):
    """Load metadata CSV and extract features for each audio file.

    CSV format:
        filepath,label
    where filepath is relative to base_dir and label is 0 (healthy) or 1 (PD).
    """
    df = pd.read_csv(metadata_path)
    if "filepath" not in df.columns or "label" not in df.columns:
        raise ValueError("metadata.csv must contain 'filepath' and 'label' columns")

    X_list, y_list = [], []

    for _, row in df.iterrows():
        rel_path = row["filepath"]
        label = int(row["label"])
        full_path = os.path.join(base_dir, rel_path)

        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"Audio file not found: {full_path}")

        y, sr = librosa.load(full_path, sr=SAMPLE_RATE, mono=True)
        feats = extract_features_from_signal(y, sr)
        X_list.append(feats)
        y_list.append(label)

    X = np.stack(X_list)
    y = np.array(y_list, dtype=np.int64)
    return X, y


def main():
    parser = argparse.ArgumentParser(description="Train PD vs healthy model.")
    parser.add_argument(
        "--metadata",
        type=str,
        default="metadata.csv",
        help="Path to metadata CSV (with filepath,label).",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory for audio filepaths in metadata.",
    )
    parser.add_argument(
        "--test-size", type=float, default=0.2, help="Test set fraction."
    )
    parser.add_argument(
        "--epochs", type=int, default=60, help="Maximum number of epochs."
    )
    parser.add_argument(
        "--batch-size", type=int, default=32, help="Batch size."
    )

    args = parser.parse_args()

    print(f"Loading dataset from {args.metadata} ...")
    X, y = load_dataset(args.metadata, args.base_dir)
    print(f"Loaded {X.shape[0]} samples with {X.shape[1]} features each.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = build_pd_model(input_dim=X_train_s.shape[1])
    model.summary()

    callbacks = [
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6, verbose=1
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=10,
            min_delta=1e-4,
            restore_best_weights=True,
            verbose=1,
        ),
    ]

    history = model.fit(
        X_train_s,
        y_train,
        validation_split=0.2,
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    y_prob = model.predict(X_test_s).ravel()
    y_pred = (y_prob >= 0.5).astype(int)

    print("\nClassification report (threshold=0.5):")
    print(classification_report(y_test, y_pred, digits=4))

    try:
        auc = roc_auc_score(y_test, y_prob)
        print(f"ROC AUC: {auc:.4f}")
    except Exception as e:
        print(f"Could not compute ROC AUC: {e}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(MODEL_PATH)
    dump(scaler, SCALER_PATH)

    print(f"\nSaved model to:  {MODEL_PATH}")
    print(f"Saved scaler to: {SCALER_PATH}")
    print("\nReminder: screening tool only; not a medical diagnosis.")

if __name__ == "__main__":
    main()
