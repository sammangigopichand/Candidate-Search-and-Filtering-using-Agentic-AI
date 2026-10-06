import os
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

RAW_DIR = os.path.join(PROJECT_ROOT, "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "processed")

os.makedirs(PROCESSED_DIR, exist_ok=True)


# ============================================================
# DATASETS TO PROCESS
# ============================================================

datasets = {
    "Skills.xlsx": "skills.csv",
    "abilities.csv": "abilities.csv",
    "essential_skills.csv": "essential_skills.csv",
    "knowledge.csv": "knowledge.csv",
    "transferable_skills.csv": "transferable_skills.csv",
    "work_activities.csv": "work_activities.csv"
}


# ============================================================
# FUNCTION TO LOAD CSV/XLSX
# ============================================================

def load_dataset(path):

    if path.lower().endswith(".csv"):
        return pd.read_csv(path, low_memory=False)

    elif path.lower().endswith(".xlsx"):
        return pd.read_excel(path)

    else:
        raise ValueError(f"Unsupported file: {path}")


# ============================================================
# PROCESS ONE SCORED DATASET
# ============================================================

def process_scored_dataset(input_file, output_file):

    input_path = os.path.join(RAW_DIR, input_file)
    output_path = os.path.join(PROCESSED_DIR, output_file)

    print("\n" + "=" * 80)
    print(f"Processing: {input_file}")
    print("=" * 80)

    df = load_dataset(input_path)

    print("Original rows:", len(df))

    # --------------------------------------------------------
    # Keep fields required by our recruitment knowledge base
    # --------------------------------------------------------

    df = df[
        [
            "O*NET-SOC Code",
            "Title",
            "Element ID",
            "Element Name",
            "Scale ID",
            "Data Value"
        ]
    ].copy()

    # --------------------------------------------------------
    # Rename columns
    # --------------------------------------------------------

    df = df.rename(
        columns={
            "O*NET-SOC Code": "onet_soc_code",
            "Title": "title",
            "Element ID": "element_id",
            "Element Name": "element_name",
            "Scale ID": "scale_id",
            "Data Value": "data_value"
        }
    )

    # --------------------------------------------------------
    # Clean text
    # --------------------------------------------------------

    text_columns = [
        "onet_soc_code",
        "title",
        "element_id",
        "element_name",
        "scale_id"
    ]

    for column in text_columns:
        df[column] = df[column].astype(str).str.strip()

    # --------------------------------------------------------
    # Keep Importance and Level
    # --------------------------------------------------------

    df = df[
        df["scale_id"].isin(["IM", "LV"])
    ].copy()

    # --------------------------------------------------------
    # Convert scores to numeric
    # --------------------------------------------------------

    df["data_value"] = pd.to_numeric(
        df["data_value"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Pivot IM/LV rows into columns
    #
    # Before:
    # Programming | IM | 4.20
    # Programming | LV | 5.50
    #
    # After:
    # Programming | 4.20 | 5.50
    # --------------------------------------------------------

    pivoted = (
        df.pivot_table(
            index=[
                "onet_soc_code",
                "title",
                "element_id",
                "element_name"
            ],
            columns="scale_id",
            values="data_value",
            aggfunc="first"
        )
        .reset_index()
    )

    # Remove pivot column name
    pivoted.columns.name = None

    # --------------------------------------------------------
    # Rename IM / LV
    # --------------------------------------------------------

    pivoted = pivoted.rename(
        columns={
            "IM": "importance",
            "LV": "level"
        }
    )

    # Some datasets could theoretically lack one scale.
    if "importance" not in pivoted.columns:
        pivoted["importance"] = None

    if "level" not in pivoted.columns:
        pivoted["level"] = None

    # --------------------------------------------------------
    # Arrange final columns
    # --------------------------------------------------------

    pivoted = pivoted[
        [
            "onet_soc_code",
            "title",
            "element_id",
            "element_name",
            "importance",
            "level"
        ]
    ]

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    pivoted = pivoted.sort_values(
        by=[
            "onet_soc_code",
            "element_id"
        ]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    pivoted.to_csv(
        output_path,
        index=False,
        encoding="utf-8"
    )

    print("Processed rows:", len(pivoted))

    print("\nSample:")
    print(pivoted.head())

    print("\nSaved:")
    print(output_path)


# ============================================================
# RUN ALL DATASETS
# ============================================================

for input_file, output_file in datasets.items():

    try:

        process_scored_dataset(
            input_file,
            output_file
        )

    except Exception as e:

        print(f"\nERROR processing {input_file}")
        print(e)


print("\n" + "=" * 80)
print("Finished processing scored O*NET datasets.")
print("=" * 80)