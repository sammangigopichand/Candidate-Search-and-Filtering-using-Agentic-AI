import os
import json


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "processed")

INPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "occupation_profiles.json"
)

OUTPUT_FILE = os.path.join(
    PROCESSED_DIR,
    "semantic_documents.json"
)


# ============================================================
# LOAD OCCUPATION PROFILES
# ============================================================

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    profiles = json.load(file)

print("Occupation profiles loaded:", len(profiles))


# ============================================================
# DOCUMENT STORAGE
# ============================================================

documents = []


def add_document(soc_code, occupation, document_type, text):

    if not text or not text.strip():
        return

    documents.append({
        "text": text.strip(),

        "metadata": {
            "onet_soc_code": soc_code,
            "occupation": occupation,
            "document_type": document_type
        }
    })


# ============================================================
# BUILD DOCUMENTS
# ============================================================

for profile in profiles:

    soc_code = profile["onet_soc_code"]
    title = profile["title"]

    # --------------------------------------------------------
    # 1. OCCUPATION DOCUMENT
    # --------------------------------------------------------

    description = profile.get("description", "")

    alternate_titles = profile.get(
        "alternate_titles",
        []
    )

    occupation_text = f"""
Occupation: {title}

Description:
{description}

Alternate Job Titles:
{", ".join(alternate_titles[:30])}
"""

    add_document(
        soc_code,
        title,
        "occupation",
        occupation_text
    )


    # --------------------------------------------------------
    # 2. SKILLS DOCUMENT
    # --------------------------------------------------------

    skills = profile.get("skills", [])

    if skills:

        skill_lines = []

        for skill in skills:

            skill_lines.append(
                f"{skill['name']} "
                f"(Importance: {skill['importance']}, "
                f"Level: {skill['level']})"
            )

        skills_text = f"""
Occupation: {title}

Required Skills:
{chr(10).join(skill_lines)}
"""

        add_document(
            soc_code,
            title,
            "skills",
            skills_text
        )



    # --------------------------------------------------------
    # 2A. ESSENTIAL SKILLS DOCUMENT
    # --------------------------------------------------------

    essential_skills = profile.get("essential_skills", [])

    if essential_skills:

        essential_skill_lines = []

        for skill in essential_skills:

            essential_skill_lines.append(
                f"{skill['name']} "
                f"(Importance: {skill['importance']}, "
                f"Level: {skill['level']})"
            )

        essential_skills_text = f"""
Occupation: {title}

Essential Skills:
{chr(10).join(essential_skill_lines)}
"""

        add_document(
            soc_code,
            title,
            "essential_skills",
            essential_skills_text
        )


    # --------------------------------------------------------
    # 2B. TRANSFERABLE SKILLS DOCUMENT
    # --------------------------------------------------------

    transferable_skills = profile.get("transferable_skills", [])

    if transferable_skills:

        transferable_skill_lines = []

        for skill in transferable_skills:

            transferable_skill_lines.append(
                f"{skill['name']} "
                f"(Importance: {skill['importance']}, "
                f"Level: {skill['level']})"
            )

        transferable_skills_text = f"""
            Occupation: {title}

            Transferable Skills:
            {chr(10).join(transferable_skill_lines)}
            """

        add_document(
            soc_code,
            title,
            "transferable_skills",
            transferable_skills_text
        )

    # --------------------------------------------------------
    # 3. TECHNOLOGY DOCUMENT
    # --------------------------------------------------------

    technologies = profile.get(
        "technology_skills",
        []
    )

    software = profile.get(
        "software_skills",
        []
    )

    technology_lines = []

    for tech in technologies:

        technology_lines.append(
            f"{tech['name']} - {tech['category']}"
        )

    for item in software:

        technology_lines.append(
            f"{item['name']} - {item['category']}"
        )

    # Remove repeated strings while preserving order
    technology_lines = list(
        dict.fromkeys(technology_lines)
    )

    if technology_lines:

        technology_text = f"""
Occupation: {title}

Technologies and Software:
{chr(10).join(technology_lines)}
"""

        add_document(
            soc_code,
            title,
            "technologies",
            technology_text
        )


    # --------------------------------------------------------
    # 4. KNOWLEDGE DOCUMENT
    # --------------------------------------------------------

    knowledge = profile.get("knowledge", [])

    if knowledge:

        knowledge_lines = []

        for item in knowledge:

            knowledge_lines.append(
                f"{item['name']} "
                f"(Importance: {item['importance']}, "
                f"Level: {item['level']})"
            )

        knowledge_text = f"""
Occupation: {title}

Required Knowledge:
{chr(10).join(knowledge_lines)}
"""

        add_document(
            soc_code,
            title,
            "knowledge",
            knowledge_text
        )


    # --------------------------------------------------------
    # 5. TASK DOCUMENT
    # --------------------------------------------------------

    tasks = profile.get("tasks", [])

    if tasks:

        task_lines = []

        for task in tasks:

            task_lines.append(
                f"{task['task_type']}: {task['task']}"
            )

        tasks_text = f"""
Occupation: {title}

Typical Tasks and Responsibilities:
{chr(10).join(task_lines)}
"""

        add_document(
            soc_code,
            title,
            "tasks",
            tasks_text
        )


    # --------------------------------------------------------
    # 6. WORK ACTIVITIES DOCUMENT
    # --------------------------------------------------------

    activities = profile.get(
        "work_activities",
        []
    )

    if activities:

        activity_lines = []

        for activity in activities:

            activity_lines.append(
                f"{activity['name']} "
                f"(Importance: {activity['importance']}, "
                f"Level: {activity['level']})"
            )

        activities_text = f"""
Occupation: {title}

Work Activities:
{chr(10).join(activity_lines)}
"""

        add_document(
            soc_code,
            title,
            "work_activities",
            activities_text
        )


# ============================================================
# SAVE
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        documents,
        file,
        indent=2,
        ensure_ascii=False
    )


print("\n" + "=" * 80)
print("SEMANTIC DOCUMENT CREATION COMPLETED")
print("=" * 80)

print("Total semantic documents:", len(documents))
print("Saved to:")
print(OUTPUT_FILE)