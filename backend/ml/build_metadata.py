# backend/ml/build_metadata.py

import os
import argparse
import pandas as pd


def parse_filename(fname: str):
    """
    Parse filenames like ID02_pd_1_2_1.wav into:
    id, health_status, hyr, updrs_ii, updrs_iii

    Example: "ID02_pd_1_2_1.wav" ->
        ("ID02", "pd", 1, 2, 1)
    """
    name = os.path.splitext(fname)[0]
    parts = name.split("_")
    if len(parts) < 5:
        raise ValueError(f"Filename does not match expected pattern: {fname}")

    subject_id = parts[0]
    hs = parts[1]  # "hc" or "pd"
    hyr = int(parts[2])
    updrs_ii = int(parts[3])
    updrs_iii = int(parts[4])

    return subject_id, hs, hyr, updrs_ii, updrs_iii


def main():
    parser = argparse.ArgumentParser(
        description="Generate metadata.csv from a local folder of MDVR-KCL WAV files."
    )
    parser.add_argument(
        "--audio-dir",
        required=True,
        help="Local directory containing WAV files (e.g. downloads of MDVR-KCL).",
    )
    parser.add_argument(
        "--bucket-name",
        required=True,
        help="Name of your GCS bucket (e.g. audisease-audio).",
    )
    parser.add_argument(
        "--output-csv",
        default="metadata.csv",
        help="Output CSV file name.",
    )
    args = parser.parse_args()

    rows = []

    for fname in os.listdir(args.audio_dir):
        if not fname.lower().endswith(".wav"):
            continue

        try:
            subject_id, hs, hyr, updrs_ii, updrs_iii = parse_filename(fname)
        except ValueError as e:
            print(f"Skipping {fname}: {e}")
            continue

        label = 1 if hs.lower() == "pd" else 0
        gcs_path = f"gs://{args.bucket_name}/{fname}"

        rows.append(
            {
                "audio_path": gcs_path,
                "label": label,
                "subject_id": subject_id,
                "health_status": hs,
                "hyr": hyr,
                "updrs_ii": updrs_ii,
                "updrs_iii": updrs_iii,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(args.output_csv, index=False)
    print(f"Wrote {len(df)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
