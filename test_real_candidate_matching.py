import json
from pathlib import Path

from app.agents.matching_agent import match_candidate
from app.services.onet_retriever import search_onet


PROFILE_DIR = Path("test_profiles")


def load_json(filename):
    file_path = PROFILE_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():

    print("\n[1/4] Loading candidate profile...")

    candidate_profile = load_json("candidate.json")

    print("\n[2/4] Loading job profile...")

    job_profile = load_json("job.json")

    print("\n[3/4] Retrieving O*NET knowledge...")

    search_query = " ".join([
        job_profile.get("job_title") or "",
        " ".join(job_profile.get("required_skills") or []),
        " ".join(job_profile.get("preferred_skills") or [])
    ])

    onet_results = search_onet(
        query=search_query,
        top_k=10
    )

    print("\n[4/4] Matching candidate against job...")

    report = match_candidate(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        onet_results=onet_results
    )

    print("\n" + "=" * 65)
    print("REAL CANDIDATE MATCHING REPORT")
    print("=" * 65)

    print("Candidate:", report["candidate_name"])
    print("Job:", report["job_title"])

    required = report["required_skills"]
    preferred = report["preferred_skills"]

    print(
        "\nRequired skills:",
        f'{required["matched_count"]}/{required["total"]}'
    )

    print(
        "Required skill coverage:",
        required["coverage_percentage"]
    )

    print("Missing required skills:", required["missing"])

    print(
        "\nPreferred skills:",
        f'{preferred["matched_count"]}/{preferred["total"]}'
    )

    print(
        "Preferred skill coverage:",
        preferred["coverage_percentage"]
    )

    print("Missing preferred skills:", preferred["missing"])

    print("\nO*NET documents retrieved:", len(report["onet_context"]))

    print("\nCandidate matching completed successfully!")


if __name__ == "__main__":
    main()