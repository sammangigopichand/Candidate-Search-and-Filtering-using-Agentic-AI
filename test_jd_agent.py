import json

from app.agents.jd_agent import process_job_description


SAMPLE_JOB_DESCRIPTION = """
Job Title: Data Scientist

Location: Chennai, India
Employment Type: Full-time

We are hiring a Data Scientist to develop machine learning
models and analyze large datasets.

Required Skills:
- Python
- SQL
- Machine Learning
- Statistical Modeling
- Pandas
- Scikit-learn

Preferred Skills:
- PyTorch
- Docker
- Cloud Computing

Experience:
Minimum 2 years and maximum 5 years of relevant experience.

Education:
Bachelor's degree in Computer Science, Data Science,
Statistics, or a related field.

Responsibilities:
- Clean and analyze structured and unstructured data.
- Develop and evaluate machine learning models.
- Collaborate with engineering and business teams.
- Deploy predictive models into production.
"""


try:
    job_profile = process_job_description(
        SAMPLE_JOB_DESCRIPTION
    )

    print("\n" + "=" * 65)
    print("STRUCTURED JOB PROFILE")
    print("=" * 65)

    print(
        json.dumps(
            job_profile,
            indent=2,
            ensure_ascii=False
        )
    )

    print("\nJob title:", job_profile["job_title"])
    print("Required skills:", len(job_profile["required_skills"]))
    print("Preferred skills:", len(job_profile["preferred_skills"]))

    print("\nJob Description Agent completed successfully!")

except Exception as error:
    print("\nJob Description Agent failed:")
    print(type(error).__name__, error)