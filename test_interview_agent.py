import json

from pathlib import Path

from app.agents.experience_agent import assess_experience

from app.agents.interview_agent import (
    generate_interview_questions,
)


# ============================================================
# CONFIGURATION
# ============================================================

PROFILE_DIR = Path("test_profiles")

OUTPUT_FILE = (
    PROFILE_DIR / "interview_questions.json"
)


# ============================================================
# LOAD JSON FILE
# ============================================================

def load_json(filename):

    file_path = PROFILE_DIR / filename

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# SAVE INTERVIEW REPORT
# ============================================================

def save_interview_report(
    interview_report: dict,
):

    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            interview_report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"\nInterview questions saved to: "
        f"{OUTPUT_FILE}"
    )


# ============================================================
# DISPLAY INTERVIEW REPORT
# ============================================================

def display_interview_report(
    interview_report: dict,
):

    print(
        "\n" + "=" * 65
    )

    print(
        "INTERVIEW AGENT REPORT"
    )

    print(
        "=" * 65
    )

    print(
        "\nTarget job:",
        interview_report["target_job"],
    )

    print(
        "Experience level:",
        interview_report["experience_level"],
    )

    questions = interview_report[
        "questions"
    ]

    print(
        "\nTotal questions:",
        len(questions),
    )

    # --------------------------------------------------------
    # DISPLAY QUESTIONS
    # --------------------------------------------------------

    for item in questions:

        print(
            "\n" + "-" * 65
        )

        print(
            "Question ID:",
            item["question_id"],
        )

        print(
            "Category:",
            item["category"],
        )

        print(
            "Difficulty:",
            item["difficulty"],
        )

        print(
            "\nQuestion:"
        )

        print(
            item["question"]
        )

        # ----------------------------------------------------
        # EXPECTED CONCEPTS
        # ----------------------------------------------------

        print(
            "\nExpected concepts:"
        )

        for concept in item[
            "expected_concepts"
        ]:

            print(
                f"  - {concept}"
            )

        # ----------------------------------------------------
        # EVALUATION CHECKLIST
        # ----------------------------------------------------

        print(
            "\nEvaluation Checklist:"
        )

        for criterion in item[
            "evaluation_criteria"
        ]:

            print(
                f"\n  {criterion['criterion_id']}: "
                f"{criterion['criterion']}"
            )

            print(
                "     [ ] Yes"
                "  [ ] Partially"
                "  [ ] No"
                "  [ ] Not Assessed"
            )

    # --------------------------------------------------------
    # DISPLAY FINAL NOTE
    # --------------------------------------------------------

    print(
        "\n" + "=" * 65
    )

    print(
        interview_report["note"]
    )

    print(
        "\nInterview question generation "
        "completed successfully!"
    )


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():

    # --------------------------------------------------------
    # STEP 1: LOAD CANDIDATE PROFILE
    # --------------------------------------------------------

    print(
        "\n[1/4] Loading candidate profile..."
    )

    candidate_profile = load_json(
        "candidate.json"
    )

    # --------------------------------------------------------
    # STEP 2: LOAD JOB PROFILE
    # --------------------------------------------------------

    print(
        "\n[2/4] Loading job profile..."
    )

    job_profile = load_json(
        "job.json"
    )

    # --------------------------------------------------------
    # STEP 3: ASSESS EXPERIENCE
    # --------------------------------------------------------

    print(
        "\n[3/4] Assessing candidate experience..."
    )

    experience_report = assess_experience(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
    )

    print(
        "Experience level:",
        experience_report.get(
            "provisional_experience_level",
            "Undetermined",
        ),
    )

    # --------------------------------------------------------
    # STEP 4: GENERATE INTERVIEW QUESTIONS
    # --------------------------------------------------------

    print(
        "\n[4/4] Generating interview questions "
        "and evaluation checklists..."
    )

    interview_report = generate_interview_questions(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        experience_report=experience_report,
    )

    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    display_interview_report(
        interview_report
    )

    # --------------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------------

    save_interview_report(
        interview_report
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()