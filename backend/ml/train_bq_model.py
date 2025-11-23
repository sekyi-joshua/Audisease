# backend/ml/train_bq_model.py

import argparse
import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
from joblib import dump

from tensorflow import keras
from tensorflow.keras import layers

from ml.gcp_utils import load_metadata_from_bigquery, load_wav_from_gcs
from ml.features import extract_features_from_signal, SAMPLE_RATE
from core.config import MODEL_DIR, MODEL_PATH, SCALER_PATH


def build_pd_model(input_dim: int):
    """Feed-forward network for binary PD vs healthy."""
    l2 = keras.regularizers.l2(1e-4)

    inp = keras.Input(shape=(input_dim,))
    x = layers.Dense(128, activation="relu", kernel_regularizer=l2)(inp)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(64, activation="relu", kernel_regularizer=l2)(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(32, activation="relu", kernel_regularizer=l2)(x)
    out = layers.Dense(1, activation="sigmoid")(x)

    model = keras.Model(inputs=inp, outputs=out, name="pd_voice_bq_model")

    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="binary_crossentropy",
        metrics=["accuracy", keras.metrics.AUC(name="auc")],
    )
    return model


def main():
    parser = argparse.ArgumentParser(
        description="Train PD vs healthy model using BigQuery + GCS audio."
    )
    parser.add_argument(
        "--bq-table-id",
        required=True,
        help=(
            "Full BigQuery table ID, e.g. "
            "'your-project-id.audisease.raw_data.parkinsons_metadata'"
        ),
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test set fraction.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=80,
        help="Max training epochs.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size.",
    )
    args = parser.parse_args()

    print(f"Loading metadata from BigQuery table: {args.bq_table_id}")
    df = load_metadata_from_bigquery(args.bq_table_id)
    print(f"Rows fetched from BigQuery: {len(df)}")

    # Expect at least 'audio_path' and 'label'
    if "audio_path" not in df.columns or "label" not in df.columns:
        raise ValueError("BigQuery table must have 'audio_path' and 'label' columns")

    X_list, y_list = [], []

    for _, row in df.iterrows():
        gcs_path = row["audio_path"]
        label = int(row["label"])

        y, sr = load_wav_from_gcs(gcs_path)
        feats = extract_features_from_signal(y, sr)
        X_list.append(feats)
        y_list.append(label)

    X = np.stack(X_list)
    y = np.array(y_list, dtype=np.int64)

    print(f"Feature matrix shape: {X.shape}, labels shape: {y.shape}")

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42, stratify=y
    )

    # Standardize features
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # Build model
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

    # Train (this is where the gradients update the weights)
    history = model.fit(
        X_train_s,
        y_train,
        validation_split=0.2,
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    # Evaluate
    y_prob = model.predict(X_test_s).ravel()
    y_pred = (y_prob >= 0.5).astype(int)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=4))

    try:
        auc = roc_auc_score(y_test, y_prob)
        print(f"ROC AUC: {auc:.4f}")
    except Exception as e:
        print(f"Could not compute ROC AUC: {e}")

    # Save model & scaler
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(MODEL_PATH)
    dump(scaler, SCALER_PATH)

    print(f"\nSaved model to:  {MODEL_PATH}")
    print(f"Saved scaler to: {SCALER_PATH}")
    print("Reminder: screening tool only, not a medical diagnosis.")


if __name__ == "__main__":
    main()
