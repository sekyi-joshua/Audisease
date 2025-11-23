# backend/ml/gcp_utils.py

import gcsfs
import soundfile as sf
import librosa
import pandas as pd
from google.cloud import bigquery

from features import SAMPLE_RATE

# GCS file system (uses your service account)
fs = gcsfs.GCSFileSystem()


def load_wav_from_gcs(gcs_path: str):
    """
    Load a WAV file directly from Google Cloud Storage.
    gcs_path example: gs://audisease-audio/ID00_hc_0_0_0.wav
    """
    with fs.open(gcs_path, "rb") as f:
        y, sr = sf.read(f)

    # Ensure mono
    if y.ndim > 1:
        # average channels if stereo
        y = y.mean(axis=1)

    # Resample if needed
    if sr != SAMPLE_RATE:
        y = librosa.resample(y, orig_sr=sr, target_sr=SAMPLE_RATE)
        sr = SAMPLE_RATE

    return y, sr


def load_metadata_from_bigquery(table_id: str) -> pd.DataFrame:
    """
    Load (audio_path, label, hyr, updrs_ii, updrs_iii) from BigQuery.

    table_id example:
        "your-project-id.audisease.raw_data.parkinsons_metadata"
    """
    client = bigquery.Client()
    query = f"""
        SELECT audio_path, label, hyr, updrs_ii, updrs_iii
        FROM `{table_id}`
    """
    df = client.query(query).to_dataframe()
    return df
