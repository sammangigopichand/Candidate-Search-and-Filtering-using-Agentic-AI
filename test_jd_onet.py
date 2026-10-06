import json

from app.agents.jd_agent import process_job_description
from app.services.onet_retriever import search_onet


SAMPLE_JOB_DESCRIPTION = """
Job Title: Data Scientist

We are hiring a Data Scientist with 2 to 5 years
of relevant experience.

Required skills:
Python, SQL, Machine Learning, Statistical Modeling,
Pandas and Scikit-learn.

Preferred skills:
PyTorch, Docker and Cloud Computing.

Responsibilities:
Develop machine learning models, analyze large datasets,
and deploy predictive models.
"""


def main():

    # STEP 1: Understand the job description

    print("\n[1/3] Extracting job requirements...")

    job_profile = process_job_description(
        SAMPLE_JOB_DESCRIPTION
    )

    # STEP 2: Prepare the O*NET search query

    print("\n[2/3] Preparing O*NET search query...")

    search_query = " ".join([
        job_profile.get("job_title") or "",
        " ".join(job_profile.get("required_skills", [])),
        " ".join(job_profile.get("preferred_skills", [])),
        " ".join(job_profile.get("responsibilities", []))
    ])

    print("\nSearch query:")
    print(search_query)

    # STEP 3: Retrieve relevant O*NET documents

    print("\n[3/3] Searching O*NET knowledge base...")

    results = search_onet(
        query=search_query,
        top_k=10
    )

    print("\n" + "=" * 65)
    print("O*NET RETRIEVAL RESULTS")
    print("=" * 65)

    for index, result in enumerate(results, start=1):

        print(f"\nResult {index}")

        print(
            "Occupation:",
            result.get("occupation")
        )

        print(
            "O*NET SOC Code:",
            result.get("onet_soc_code")
        )

        print(
            "Document Type:",
            result.get("document_type")
        )

        print(
            "Similarity Score:",
            result.get("score")
        )

        print(
            "Text:",
            result.get("text", "")[:400]
        )

        print("-" * 65)

    print("\nJD to O*NET integration test completed!")


if __name__ == "__main__":
    main()