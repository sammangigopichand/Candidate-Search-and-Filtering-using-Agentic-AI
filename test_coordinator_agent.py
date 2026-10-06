from pathlib import Path


from app.agents.coordinator_agent import (
    process_candidate_workflow,
)


# ============================================================
# TEST RESUME
# ============================================================


from pathlib import Path

from app.agents.coordinator_agent import (
    process_candidate_workflow,
)


# ============================================================
# FIND TEST RESUME
# ============================================================

RESUME_FOLDER = Path("test_resumes")

pdf_files = list(
    RESUME_FOLDER.glob("*.pdf")
)

docx_files = list(
    RESUME_FOLDER.glob("*.docx")
)

resume_files = pdf_files + docx_files

if not resume_files:
    raise FileNotFoundError(
        "No PDF or DOCX resume found inside "
        f"{RESUME_FOLDER.resolve()}"
    )

RESUME_PATH = str(
    resume_files[0]
)

print(
    "Using resume:",
    RESUME_PATH,
)



# RESUME_PATH = (
#     "test_resumes/"
#     "Sammangi_Gopi_Chand_AI&ML.pdf"
# )


# ============================================================
# SAMPLE JOB PROFILE
# ============================================================

job_profile = {
    "job_title": "Data Scientist",

    "role_summary": (
        "Develop machine learning models and "
        "data-driven applications."
    ),

    "required_skills": [
        "Python",
        "Machine Learning",
        "Pandas",
        "NumPy",
        "Scikit-learn",
        "SQL",
    ],

    "preferred_skills": [
        "TensorFlow",
        "PyTorch",
        "Docker",
        "FastAPI",
    ],

    "technologies": [
        "Python",
        "Scikit-learn",
        "TensorFlow",
        "PyTorch",
    ],

    "minimum_experience_years": 0,

    "maximum_experience_years": 3,

    "education": [
        "Computer Science",
        "Artificial Intelligence",
        "Machine Learning",
    ],

    "required_certifications": [],

    "preferred_certifications": [],

    "responsibilities": [
        "Develop machine learning models",
        "Perform data preprocessing",
        "Evaluate ML models",
        "Build data-driven applications",
    ],
}


# ============================================================
# RUN COORDINATOR
# ============================================================

print("\n========================================")
print("RECRUITMENT COORDINATOR TEST")
print("========================================")


result = process_candidate_workflow(
    resume_path=RESUME_PATH,
    job_profile=job_profile,
)


# ============================================================
# WORKFLOW RESULT
# ============================================================

print("\n========================================")
print("WORKFLOW STATUS")
print("========================================")

print(
    "Stage:",
    result.get("current_stage"),
)

print(
    "Status:",
    result.get("workflow_status"),
)

print(
    "Error:",
    result.get("error"),
)


# ============================================================
# CANDIDATE
# ============================================================

candidate = result.get(
    "candidate_profile",
    {},
)

print("\n========================================")
print("CANDIDATE PROFILE")
print("========================================")

print(
    "Name:",
    candidate.get("name"),
)

print(
    "Skills:",
    candidate.get("skills"),
)


# ============================================================
# MATCHING
# ============================================================

matching = result.get(
    "matching_report",
    {},
)

print("\n========================================")
print("MATCHING REPORT")
print("========================================")

required = matching.get(
    "required_skills",
    {},
)

print(
    "Coverage:",
    required.get(
        "coverage_percentage"
    ),
)

print(
    "Matched:",
    required.get("matched"),
)

print(
    "Missing:",
    required.get("missing"),
)


# ============================================================
# EXPERIENCE
# ============================================================

experience = result.get(
    "experience_report",
    {},
)

print("\n========================================")
print("EXPERIENCE REPORT")
print("========================================")

print(
    "Experience Level:",
    experience.get(
        "provisional_experience_level"
    ),
)

print(
    "Total Experience:",
    experience.get(
        "total_experience_years"
    ),
)

print(
    "Relevant Experience:",
    experience.get(
        "documented_relevant_experience_years"
    ),
)



print("\n========================================")
print("ASSESSED ROLES")
print("========================================")

experience_report = result.get(
    "experience_report",
    {}
)

for role in experience_report.get(
    "assessed_roles",
    []
):
    print("\nRole:", role.get("job_title"))
    print("Company:", role.get("company"))
    print("Start:", role.get("start_date"))
    print("End:", role.get("end_date"))
    print(
        "Relevance:",
        role.get("relevance")
    )

print("\n========================================")
print("UNVERIFIED ROLES")
print("========================================")

for role in experience_report.get(
    "unverified_roles",
    []
):
    print(role)


# ============================================================
# FINAL
# ============================================================

print("\n========================================")

if result.get("error"):

    print(
        "WORKFLOW FAILED:",
        result["error"],
    )

else:

    print(
        "CANDIDATE READY FOR RECRUITER REVIEW"
    )

print("========================================")




print("\n========================================")
print("RAW EXPERIENCE RECORDS")
print("========================================")

candidate_profile = result.get(
    "candidate_profile",
    {}
)

for index, role in enumerate(
    candidate_profile.get("experience", []),
    start=1,
):
    print(f"\nROLE {index}")
    print(role)