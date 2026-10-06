import os
import json
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "processed")

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "occupation_profiles.json"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_csv(filename):
    path = os.path.join(PROCESSED_DIR, filename)
    print(f"Loading {filename}...")
    return pd.read_csv(path, low_memory=False)


occupations = load_csv("occupations.csv")

skills = load_csv("skills.csv")
abilities = load_csv("abilities.csv")
essential_skills = load_csv("essential_skills.csv")
transferable_skills = load_csv("transferable_skills.csv")
knowledge = load_csv("knowledge.csv")
work_activities = load_csv("work_activities.csv")

technology = load_csv("technology_skills.csv")
software = load_csv("software_skills.csv")

job_titles = load_csv("job_titles.csv")
tasks = load_csv("tasks.csv")

education = load_csv("education.csv")
training_experience = load_csv("training_experience.csv")
job_zones = load_csv("job_zones.csv")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_value(value):

    if pd.isna(value):
        return None

    # Convert numpy values into normal Python values
    if hasattr(value, "item"):
        return value.item()

    return value


def get_scored_features(df, soc_code):

    rows = df[
        df["onet_soc_code"] == soc_code
    ]

    result = []

    for _, row in rows.iterrows():

        result.append({
            "element_id": safe_value(row["element_id"]),
            "name": safe_value(row["element_name"]),
            "importance": safe_value(row["importance"]),
            "level": safe_value(row["level"])
        })

    return result


# ============================================================
# BUILD PROFILES
# ============================================================

profiles = []

total = len(occupations)

print("\nBuilding occupation profiles...")
print("Total occupations:", total)


for index, occupation in occupations.iterrows():

    soc_code = occupation["onet_soc_code"]

    profile = {
        "onet_soc_code": soc_code,

        "title": safe_value(
            occupation["title"]
        ),

        "description": safe_value(
            occupation["description"]
        )
    }


    # --------------------------------------------------------
    # JOB TITLES
    # --------------------------------------------------------

    rows = job_titles[
        job_titles["onet_soc_code"] == soc_code
    ]

    profile["alternate_titles"] = (
        rows["job_title"]
        .dropna()
        .drop_duplicates()
        .tolist()
    )


    # --------------------------------------------------------
    # SCORED FEATURES
    # --------------------------------------------------------

    profile["skills"] = get_scored_features(
        skills,
        soc_code
    )

    profile["essential_skills"] = get_scored_features(
        essential_skills,
        soc_code
    )

    profile["transferable_skills"] = get_scored_features(
        transferable_skills,
        soc_code
    )

    profile["knowledge"] = get_scored_features(
        knowledge,
        soc_code
    )

    profile["abilities"] = get_scored_features(
        abilities,
        soc_code
    )

    profile["work_activities"] = get_scored_features(
        work_activities,
        soc_code
    )


    # --------------------------------------------------------
    # TECHNOLOGY SKILLS
    # --------------------------------------------------------

    rows = technology[
        technology["onet_soc_code"] == soc_code
    ]

    technologies = []

    for _, row in rows.iterrows():

        technologies.append({
            "name": safe_value(row["technology"]),
            "category": safe_value(row["category"]),
            "hot_technology": bool(
                row["hot_technology"]
            ),
            "in_demand": bool(
                row["in_demand"]
            )
        })

    profile["technology_skills"] = technologies


    # --------------------------------------------------------
    # SOFTWARE SKILLS
    # --------------------------------------------------------

    rows = software[
        software["onet_soc_code"] == soc_code
    ]

    software_list = []

    for _, row in rows.iterrows():

        software_list.append({
            "name": safe_value(row["software"]),
            "category": safe_value(row["category"]),
            "hot_technology": bool(
                row["hot_technology"]
            ),
            "in_demand": bool(
                row["in_demand"]
            )
        })

    profile["software_skills"] = software_list


    # --------------------------------------------------------
    # TASKS
    # --------------------------------------------------------

    rows = tasks[
        tasks["onet_soc_code"] == soc_code
    ]

    task_list = []

    for _, row in rows.iterrows():

        task_list.append({
            "task_id": safe_value(row["task_id"]),
            "task": safe_value(row["task"]),
            "task_type": safe_value(row["task_type"])
        })

    profile["tasks"] = task_list


    # --------------------------------------------------------
    # EDUCATION
    # --------------------------------------------------------

    rows = education[
        education["onet_soc_code"] == soc_code
    ]

    education_list = []

    for _, row in rows.iterrows():

        education_list.append({
            "element": safe_value(row["element_name"]),
            "category": safe_value(row["category"]),
            "description": safe_value(
                row["category_description"]
            ),
            "value": safe_value(row["data_value"])
        })

    profile["education"] = education_list


    # --------------------------------------------------------
    # TRAINING / EXPERIENCE
    # --------------------------------------------------------

    rows = training_experience[
        training_experience["onet_soc_code"] == soc_code
    ]

    experience_list = []

    for _, row in rows.iterrows():

        experience_list.append({
            "element": safe_value(row["element_name"]),
            "category": safe_value(row["category"]),
            "description": safe_value(
                row["category_description"]
            ),
            "value": safe_value(row["data_value"])
        })

    profile["training_experience"] = experience_list


    # --------------------------------------------------------
    # JOB ZONE
    # --------------------------------------------------------

    rows = job_zones[
        job_zones["onet_soc_code"] == soc_code
    ]

    if not rows.empty:

        row = rows.iloc[0]

        profile["job_zone"] = {
            "zone": safe_value(row["job_zone"]),
            "name": safe_value(row["zone_name"]),
            "experience": safe_value(row["experience"]),
            "education": safe_value(row["education"]),
            "training": safe_value(row["job_training"]),
            "svp_range": safe_value(row["svp_range"])
        }

    else:

        profile["job_zone"] = None


    # --------------------------------------------------------
    # ADD PROFILE
    # --------------------------------------------------------

    profiles.append(profile)

    if (index + 1) % 100 == 0:
        print(
            f"Processed {index + 1}/{total}"
        )


# ============================================================
# SAVE JSON
# ============================================================

print("\nSaving occupation profiles...")

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        profiles,
        file,
        indent=2,
        ensure_ascii=False
    )


print("\n" + "=" * 80)
print("PROFILE BUILD COMPLETED")
print("=" * 80)

print("Total profiles:", len(profiles))
print("Saved to:")
print(OUTPUT_FILE)