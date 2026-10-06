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
# CLEAN JOB TITLES
# ============================================================

def clean_job_titles():

    input_path = os.path.join(
        RAW_DIR,
        "Job Titles.xlsx"
    )

    output_path = os.path.join(
        PROCESSED_DIR,
        "job_titles.csv"
    )

    print("\nProcessing Job Titles...")

    df = pd.read_excel(input_path)

    print("Original rows:", len(df))

    # Keep required columns
    df = df[
        [
            "O*NET-SOC Code",
            "Title",
            "Job Title",
            "Short Title"
        ]
    ].copy()

    # Rename columns
    df = df.rename(
        columns={
            "O*NET-SOC Code": "onet_soc_code",
            "Title": "occupation_title",
            "Job Title": "job_title",
            "Short Title": "short_title"
        }
    )

    # Clean text
    for column in [
        "onet_soc_code",
        "occupation_title",
        "job_title"
    ]:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
        )

    # Short Title contains many missing values.
    # Missing short titles are valid, so keep them as empty strings.
    df["short_title"] = (
        df["short_title"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Remove duplicate occupation/job-title combinations
    df = df.drop_duplicates(
        subset=[
            "onet_soc_code",
            "job_title"
        ]
    )

    # Sort
    df = df.sort_values(
        by=[
            "onet_soc_code",
            "job_title"
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
# CLEAN TASK STATEMENTS
# ============================================================

def clean_tasks():

    input_path = os.path.join(
        RAW_DIR,
        "Task Statements.xlsx"
    )

    output_path = os.path.join(
        PROCESSED_DIR,
        "tasks.csv"
    )

    print("\nProcessing Task Statements...")

    df = pd.read_excel(input_path)

    print("Original rows:", len(df))

    # Keep required columns
    df = df[
        [
            "O*NET-SOC Code",
            "Title",
            "Task ID",
            "Task",
            "Task Type"
        ]
    ].copy()

    # Rename
    df = df.rename(
        columns={
            "O*NET-SOC Code": "onet_soc_code",
            "Title": "title",
            "Task ID": "task_id",
            "Task": "task",
            "Task Type": "task_type"
        }
    )

    # Clean text
    for column in [
        "onet_soc_code",
        "title",
        "task"
    ]:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
        )

    # Some Task Type values are missing.
    df["task_type"] = (
        df["task_type"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    # Remove duplicate tasks
    df = df.drop_duplicates(
        subset=[
            "onet_soc_code",
            "task_id"
        ]
    )

    # Sort
    df = df.sort_values(
        by=[
            "onet_soc_code",
            "task_id"
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
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("STARTING JOB TITLE AND TASK PREPROCESSING")
    print("=" * 80)

    clean_job_titles()

    clean_tasks()

    print("\n" + "=" * 80)
    print("PREPROCESSING COMPLETED SUCCESSFULLY")
    print("=" * 80)