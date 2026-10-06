import os
import pandas as pd

# Location of this Python file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Raw dataset folder
DATA_FOLDER = os.path.join(PROJECT_ROOT, "raw")

print("Looking for datasets in:")
print(DATA_FOLDER)

if not os.path.exists(DATA_FOLDER):
    print("ERROR: Raw folder does not exist.")
    exit()

files_found = 0

for root, dirs, files in os.walk(DATA_FOLDER):

    for filename in files:

        path = os.path.join(root, filename)

        try:

            if filename.lower().endswith(".csv"):
                df = pd.read_csv(path, low_memory=False)

            elif filename.lower().endswith(".xlsx"):
                df = pd.read_excel(path)

            else:
                continue

            files_found += 1

            print("\n")
            print("=" * 100)
            print(f"FILE: {filename}")
            print("=" * 100)

            print(f"Shape: {df.shape}")

            print("\nColumns:")

            for column in df.columns:
                print(f"  - {column}")

            print("\nFirst 3 rows:")
            print(df.head(3).to_string())

            print("\nMissing values:")
            print(df.isnull().sum())

            print("\nDuplicate rows:")
            print(df.duplicated().sum())

        except Exception as e:

            print("\n" + "=" * 100)
            print(f"ERROR reading: {filename}")
            print(f"Path: {path}")
            print(f"Error: {e}")


print("\n" + "=" * 100)
print(f"Total datasets successfully inspected: {files_found}")
print("=" * 100)