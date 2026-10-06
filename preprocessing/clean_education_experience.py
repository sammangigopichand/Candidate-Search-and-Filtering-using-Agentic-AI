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
# CLEAN EDUCATION
# ============================================================

def clean_education():

    print("\nProcessing Education...")

    education = pd.read_excel(
        os.path.join(RAW_DIR, "Education.xlsx")
    )

    categories = pd.read_excel(
        os.path.join(RAW_DIR, "Education Categories.xlsx")
    )

    print("Education rows:", len(education))

    # Keep useful columns
    education = education[
        [
            "O*NET-SOC Code",
            "Title",
            "Element ID",
            "Element Name",
            "Scale ID",
            "Category",
            "Data Value"
        ]
    ].copy()

    categories = categories[
        [
            "Element ID",
            "Scale ID",
            "Category",
            "Category Description"
        ]
    ].copy()

    # Category contains NaN for some non-category rows.
    # Only category-based records are useful for this join.
    education = education.dropna(subset=["Category"]).copy()

    education["Category"] = education["Category"].astype(int)
    categories["Category"] = categories["Category"].astype(int)

    # Join category number with human-readable meaning
    education = education.merge(
        categories,
        on=[
            "Element ID",
            "Scale ID",
            "Category"
        ],
        how="left"
    )

    education = education.rename(
        columns={
            "O*NET-SOC Code": "onet_soc_code",
            "Title": "title",
            "Element ID": "element_id",
            "Element Name": "element_name",
            "Scale ID": "scale_id",
            "Category": "category",
            "Data Value": "data_value",
            "Category Description": "category_description"
        }
    )

    for col in [
        "onet_soc_code",
        "title",
        "element_id",
        "element_name",
        "scale_id"
    ]:
        education[col] = education[col].astype(str).str.strip()

    education["category_description"] = (
        education["category_description"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    education = education.drop_duplicates()

    output = os.path.join(
        PROCESSED_DIR,
        "education.csv"
    )

    education.to_csv(
        output,
        index=False,
        encoding="utf-8"
    )

    print("Processed education rows:", len(education))
    print("Saved:", output)


# ============================================================
# CLEAN TRAINING AND EXPERIENCE
# ============================================================

def clean_training_experience():

    print("\nProcessing Training and Experience...")

    experience = pd.read_excel(
        os.path.join(
            RAW_DIR,
            "Training and Experience.xlsx"
        )
    )

    categories = pd.read_excel(
        os.path.join(
            RAW_DIR,
            "Training and Experience Categories.xlsx"
        )
    )

    print("Training/Experience rows:", len(experience))

    experience = experience[
        [
            "O*NET-SOC Code",
            "Title",
            "Element ID",
            "Element Name",
            "Scale ID",
            "Category",
            "Data Value"
        ]
    ].copy()

    categories = categories[
        [
            "Element ID",
            "Scale ID",
            "Category",
            "Category Description"
        ]
    ].copy()

    experience = experience.dropna(
        subset=["Category"]
    ).copy()

    experience["Category"] = (
        experience["Category"].astype(int)
    )

    categories["Category"] = (
        categories["Category"].astype(int)
    )

    experience = experience.merge(
        categories,
        on=[
            "Element ID",
            "Scale ID",
            "Category"
        ],
        how="left"
    )

    experience = experience.rename(
        columns={
            "O*NET-SOC Code": "onet_soc_code",
            "Title": "title",
            "Element ID": "element_id",
            "Element Name": "element_name",
            "Scale ID": "scale_id",
            "Category": "category",
            "Data Value": "data_value",
            "Category Description": "category_description"
        }
    )

    for col in [
        "onet_soc_code",
        "title",
        "element_id",
        "element_name",
        "scale_id"
    ]:
        experience[col] = (
            experience[col]
            .astype(str)
            .str.strip()
        )

    experience["category_description"] = (
        experience["category_description"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    experience = experience.drop_duplicates()

    output = os.path.join(
        PROCESSED_DIR,
        "training_experience.csv"
    )

    experience.to_csv(
        output,
        index=False,
        encoding="utf-8"
    )

    print(
        "Processed training/experience rows:",
        len(experience)
    )

    print("Saved:", output)


# ============================================================
# CLEAN JOB ZONES
# ============================================================

def clean_job_zones():

    print("\nProcessing Job Zones...")

    zones = pd.read_excel(
        os.path.join(
            RAW_DIR,
            "Job Zones.xlsx"
        )
    )

    reference = pd.read_excel(
        os.path.join(
            RAW_DIR,
            "Job Zone Reference.xlsx"
        )
    )

    print("Job Zone rows:", len(zones))

    zones = zones[
        [
            "O*NET-SOC Code",
            "Title",
            "Job Zone"
        ]
    ].copy()

    reference = reference[
        [
            "Job Zone",
            "Name",
            "Experience",
            "Education",
            "Job Training",
            "SVP Range"
        ]
    ].copy()

    # Add Job Zone description/details
    zones = zones.merge(
        reference,
        on="Job Zone",
        how="left"
    )

    zones = zones.rename(
        columns={
            "O*NET-SOC Code": "onet_soc_code",
            "Title": "title",
            "Job Zone": "job_zone",
            "Name": "zone_name",
            "Experience": "experience",
            "Education": "education",
            "Job Training": "job_training",
            "SVP Range": "svp_range"
        }
    )

    zones["onet_soc_code"] = (
        zones["onet_soc_code"]
        .astype(str)
        .str.strip()
    )

    zones["title"] = (
        zones["title"]
        .astype(str)
        .str.strip()
    )

    zones = zones.drop_duplicates(
        subset=["onet_soc_code"]
    )

    zones = zones.sort_values(
        "onet_soc_code"
    ).reset_index(drop=True)

    output = os.path.join(
        PROCESSED_DIR,
        "job_zones.csv"
    )

    zones.to_csv(
        output,
        index=False,
        encoding="utf-8"
    )

    print("Processed Job Zone rows:", len(zones))
    print("Saved:", output)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("STARTING EDUCATION / EXPERIENCE / JOB ZONE PROCESSING")
    print("=" * 80)

    clean_education()

    clean_training_experience()

    clean_job_zones()

    print("\n" + "=" * 80)
    print("STAGE 5 COMPLETED SUCCESSFULLY")
    print("=" * 80)