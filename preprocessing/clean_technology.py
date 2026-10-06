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
# PROCESS TECHNOLOGY SKILLS
# ============================================================

def process_technology_skills():

    input_path = os.path.join(
        RAW_DIR,
        "Technology Skills.xlsx"
    )

    output_path = os.path.join(
        PROCESSED_DIR,
        "technology_skills.csv"
    )

    print("\nProcessing Technology Skills...")

    df = pd.read_excel(input_path)

    print("Original rows:", len(df))

    # Keep useful columns
    df = df[
        [
            "O*NET-SOC Code",
            "Title",
            "Example",
            "Commodity Code",
            "Commodity Title",
            "Hot Technology",
            "In Demand"
        ]
    ].copy()

    # Rename
    df = df.rename(
        columns={
            "O*NET-SOC Code": "onet_soc_code",
            "Title": "title",
            "Example": "technology",
            "Commodity Code": "commodity_code",
            "Commodity Title": "category",
            "Hot Technology": "hot_technology",
            "In Demand": "in_demand"
        }
    )

    # Clean strings
    text_columns = [
        "onet_soc_code",
        "title",
        "technology",
        "category"
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
        )

    # Convert Y/N to boolean
    df["hot_technology"] = (
        df["hot_technology"]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("Y")
    )

    df["in_demand"] = (
        df["in_demand"]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("Y")
    )

    # Remove duplicates
    df = df.drop_duplicates(
        subset=[
            "onet_soc_code",
            "technology"
        ]
    )

    # Sort
    df = df.sort_values(
        by=[
            "onet_soc_code",
            "technology"
        ]
    ).reset_index(drop=True)

    # Save
    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8"
    )

    print("Processed rows:", len(df))

    print("\nSample:")
    print(df.head())

    print("\nSaved:")
    print(output_path)


# ============================================================
# PROCESS SOFTWARE SKILLS
# ============================================================

def process_software_skills():

    input_path = os.path.join(
        RAW_DIR,
        "Software Skills.xlsx"
    )

    output_path = os.path.join(
        PROCESSED_DIR,
        "software_skills.csv"
    )

    print("\nProcessing Software Skills...")

    df = pd.read_excel(input_path)

    print("Original rows:", len(df))

    df = df[
        [
            "O*NET-SOC Code",
            "Title",
            "Workplace Example",
            "Element ID",
            "Element Name",
            "Hot Technology",
            "In Demand"
        ]
    ].copy()

    df = df.rename(
        columns={
            "O*NET-SOC Code": "onet_soc_code",
            "Title": "title",
            "Workplace Example": "software",
            "Element ID": "element_id",
            "Element Name": "category",
            "Hot Technology": "hot_technology",
            "In Demand": "in_demand"
        }
    )

    text_columns = [
        "onet_soc_code",
        "title",
        "software",
        "element_id",
        "category"
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
        )

    # Y/N -> True/False
    df["hot_technology"] = (
        df["hot_technology"]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("Y")
    )

    df["in_demand"] = (
        df["in_demand"]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("Y")
    )

    df = df.drop_duplicates(
        subset=[
            "onet_soc_code",
            "software"
        ]
    )

    df = df.sort_values(
        by=[
            "onet_soc_code",
            "software"
        ]
    ).reset_index(drop=True)

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8"
    )

    print("Processed rows:", len(df))

    print("\nSample:")
    print(df.head())

    print("\nSaved:")
    print(output_path)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    process_technology_skills()

    process_software_skills()

    print("\n" + "=" * 80)
    print("Technology preprocessing completed.")
    print("=" * 80)