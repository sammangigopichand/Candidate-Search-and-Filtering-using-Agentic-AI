from app.services.resume_parser import parse_resume


RESUME_PATH = "test_resumes\Sammangi_Gopi_Chand_AI&ML.pdf"


try:

    resume_text = parse_resume(
        RESUME_PATH
    )

    print("=" * 80)
    print("RESUME TEXT EXTRACTION")
    print("=" * 80)

    print(resume_text)

    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)

    print(
        "Characters extracted:",
        len(resume_text)
    )

    print(
        "Words extracted:",
        len(resume_text.split())
    )

    print("\nResume parsed successfully!")


except Exception as error:

    print(
        "Resume parsing failed:",
        error
    )