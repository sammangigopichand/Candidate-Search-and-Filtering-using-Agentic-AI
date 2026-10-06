import json

from app.agents.matching_agent import match_candidate


# ============================================================
# SAMPLE CANDIDATE PROFILE
# ============================================================

CANDIDATE_PROFILE = {
    "name": "Sample Candidate",

    "skills": [
        "Python",
        "SQL",
        "Machine Learning",
        "Pandas",
        "Scikit-learn",
        "PyTorch",
        "Docker"
    ],

    "education": [
        {
            "degree": "B.Tech",
            "field": "Computer Science",
            "institution": "Sample University",
            "start_date": "2020",
            "end_date": "2024"
        }
    ],

    "experience": [
        {
            "job_title": "Data Analyst",
            "company": "Sample Company",
            "start_date": "2024",
            "end_date": None,
            "responsibilities": [],
            "technologies": [
                "Python",
                "SQL"
            ]
        }
    ],

    "projects": [
        {
            "name": "Machine Learning Project",
            "description": "Developed a classification model.",
            "technologies": [
                "Scikit-learn",
                "Pandas"
            ]
        }
    ],

    "certifications": []
}


# ============================================================
# SAMPLE JOB PROFILE
# ============================================================

JOB_PROFILE = {
    "job_title": "Data Scientist",

    "required_skills": [
        "Python",
        "SQL",
        "Machine Learning",
        "Statistical Modeling",
        "Pandas",
        "Scikit-learn"
    ],

    "preferred_skills": [
        "PyTorch",
        "Docker",
        "Cloud Computing"
    ],

    "minimum_experience_years": 2,
    "maximum_experience_years": 5,

    "education": [
        "Bachelor's degree in Computer Science or a related field"
    ]
}


# ============================================================
# TEST
# ============================================================

def main():

    print("\nRunning Candidate Matching Agent...")

    report = match_candidate(
        candidate_profile=CANDIDATE_PROFILE,
        job_profile=JOB_PROFILE,
        onet_results=[]
    )

    print("\n" + "=" * 65)
    print("CANDIDATE MATCHING REPORT")
    print("=" * 65)

    print(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False
        )
    )

    print("\nRequired skill coverage:",
          report["required_skills"]["coverage_percentage"])

    print("Preferred skill coverage:",
          report["preferred_skills"]["coverage_percentage"])

    print("\nCandidate Matching Agent completed successfully!")


if __name__ == "__main__":
    main()