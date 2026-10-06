import json

from app.agents.resume_agent import process_resume


RESUME_PATH = "test_resumes\Sammangi_Gopi_Chand_AI&ML.pdf"


try:

    candidate = process_resume(
        RESUME_PATH
    )

    print("\n" + "=" * 80)
    print("STRUCTURED CANDIDATE PROFILE")
    print("=" * 80)

    print(
        json.dumps(
            candidate,
            indent=2,
            ensure_ascii=False
        )
    )

    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)

    print("Name:", candidate.get("name"))

    print(
        "Skills:",
        len(candidate.get("skills", []))
    )

    print(
        "Education records:",
        len(candidate.get("education", []))
    )

    print(
        "Experience records:",
        len(candidate.get("experience", []))
    )

    print(
        "Projects:",
        len(candidate.get("projects", []))
    )

    print(
        "Certifications:",
        len(candidate.get("certifications", []))
    )

    print("\nResume Understanding Agent completed successfully!")


except Exception as error:

    print(
        "\nResume Understanding Agent failed:"
    )

    print(error)