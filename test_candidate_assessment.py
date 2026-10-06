import json
from pathlib import Path

from app.agents.matching_agent import match_candidate
from app.agents.experience_agent import assess_experience
from app.services.onet_retriever import search_onet


PROFILE_DIR = Path("test_profiles")


def load_json(filename):
    with open(PROFILE_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    print("\n[1/4] Loading candidate and job profiles...")
    candidate = load_json("candidate.json")
    job = load_json("job.json")

    print("\n[2/4] Retrieving O*NET context...")
    query = " ".join(
        [
            job.get("job_title") or "",
            " ".join(job.get("required_skills") or []),
            " ".join(job.get("preferred_skills") or []),
        ]
    )
    onet_results = search_onet(query=query, top_k=10)

    print("\n[3/4] Running Candidate Matching Agent...")
    matching = match_candidate(
        candidate_profile=candidate,
        job_profile=job,
        onet_results=onet_results,
    )

    print("\n[4/4] Running Experience-Level Agent...")
    experience = assess_experience(
        candidate_profile=candidate,
        job_profile=job,
    )

    print("\n" + "=" * 65)
    print("COMBINED CANDIDATE ASSESSMENT")
    print("=" * 65)

    print("Candidate:", candidate.get("name"))
    print("Target job:", job.get("job_title"))

    required = matching["required_skills"]
    preferred = matching["preferred_skills"]

    print("\n--- SKILL MATCHING ---")
    print(
        "Required skills:",
        f'{required["matched_count"]}/{required["total"]}',
    )
    print("Required-skill coverage:", required["coverage_percentage"])
    print("Unmatched required skills:", required["missing"])

    print(
        "\nPreferred skills:",
        f'{preferred["matched_count"]}/{preferred["total"]}',
    )
    print("Preferred-skill coverage:", preferred["coverage_percentage"])
    print("Unmatched preferred skills:", preferred["missing"])

    print("\nO*NET documents retrieved:", len(matching["onet_context"]))

    print("\n--- EXPERIENCE ASSESSMENT ---")
    total = experience["total_experience_years"]

    print(
        "Estimated total employment:",
        f'{total["minimum"]}–{total["maximum"]} years',
    )
    print(
        "Provisional experience level:",
        experience["provisional_experience_level"],
    )
    print(
        "Possible experience levels:",
        ", ".join(experience["possible_experience_levels"]),
    )

    relevant_roles = [
        role
        for role in experience["assessed_roles"]
        if role["relevance"]["status"] == "documented_overlap"
    ]

    if relevant_roles:
        relevant = experience["documented_relevant_experience_years"]
        print(
            "Employment with documented role overlap:",
            f'{relevant["minimum"]}–{relevant["maximum"]} years',
        )
    else:
        print(
            "Relevant employment:",
            "Not established from the available role details",
        )

    print("\n--- REVIEW NOTES ---")
    print(
        "Skill coverage reflects documented skill-name matches; "
        "it is not a final suitability score."
    )
    print(
        "Employment dates and role relevance require verification "
        "before making recruitment decisions."
    )

    print("\nCombined assessment completed successfully!")


if __name__ == "__main__":
    main()