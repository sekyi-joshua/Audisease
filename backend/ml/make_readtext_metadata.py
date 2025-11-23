# backend/ml/make_readtext_metadata.py

import os
import csv

# CHANGE THIS to your actual ReadText folder:
DATA_DIR = r"C:\Users\manin\Downloads\parkinsons"

# We will write metadata.csv into the backend folder:
OUTPUT_CSV = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # go up from ml/ to backend/
    "metadata_readtext.csv"
)

def main():
    rows = []

    # Expect subfolders HC and PD inside DATA_DIR
    for label_name, label_value in [("HC", 0), ("PD", 1)]:
        subdir = os.path.join(DATA_DIR, label_name)
        if not os.path.isdir(subdir):
            print(f"Warning: folder not found: {subdir}")
            continue

        for fname in os.listdir(subdir):
            if not fname.lower().endswith(".wav"):
                continue

            rel_path = os.path.join(label_name, fname)  # e.g. "HC\\ID00_hc_0_0_0.wav"
            rows.append({"filepath": rel_path, "label": label_value})

    if not rows:
        print("No WAV files found. Check DATA_DIR path.")
        return

    # Write CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filepath", "label"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
