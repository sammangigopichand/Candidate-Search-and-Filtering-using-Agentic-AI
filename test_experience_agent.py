import json
from pathlib import Path

from app.agents.experience_agent import assess_experience


PROFILE_DIR = Path("test_profiles")


def load_json(filename):
    file_path = PROFILE_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    print("\n[1/3] Loading candidate profile...")
    candidate_profile = load_json("candidate.json")

    print("\n[2/3] Loading job profile...")
    job_profile = load_json("job.json")

    print("\n[3/3] Assessing professional experience...")
    report = assess_experience(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
    )

    print("\n" + "=" * 65)
    print("EXPERIENCE-LEVEL AGENT REPORT")
    print("=" * 65)

    print("Candidate:", report["candidate_name"])
    print("Target job:", report["target_job"])
    print("Reference date:", report["reference_date"])

    total = report["total_experience_years"]
    relevant = report["documented_relevant_experience_years"]

    print(
        "\nTotal documented employment:",
        f'{total["minimum"]}–{total["maximum"]} years',
    )

    print(
        "Employment with documented role overlap:",
        f'{relevant["minimum"]}–{relevant["maximum"]} years',
    )

    print(
        "\nProvisional experience level:",
        report["provisional_experience_level"],
    )

    print(
        "Possible experience levels:",
        ", ".join(report["possible_experience_levels"]),
    )

    print("\nAssessed roles:")

    for role in report["assessed_roles"]:
        print(
            f'- {role["job_title"]} at {role["company"]} '
            f'({role["start_date"]} to {role["end_date"]})'
        )
        print("  Relevance:", role["relevance"]["status"])
        print("  Evidence:", role["relevance"]["evidence"])

    if report["unverified_roles"]:
        print("\nRoles requiring date verification:")

        for role in report["unverified_roles"]:
            print(
                f'- {role["job_title"]} at {role["company"]}: '
                f'{role["reason"]}'
            )

    print("\nNote:", report["note"])
    print("\nExperience assessment completed successfully!")


if __name__ == "__main__":
    main()