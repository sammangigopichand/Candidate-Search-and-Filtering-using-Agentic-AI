import re
import json
import urllib.request
import urllib.error


from app.services.resume_parser import parse_resume


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"

# MODEL = "llama3.1:8b"
MODEL = "llama3.2:3b"

OLLAMA_TIMEOUT = 900


# ============================================================
# CALL OLLAMA
# ============================================================

def call_ollama(prompt: str) -> dict:

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "num_predict": 3500,
        }
    }

    data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    print("\nCalling Ollama model:", MODEL)

    try:

        with urllib.request.urlopen(
            request,
            timeout=OLLAMA_TIMEOUT
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Could not connect to Ollama: {error}"
        )

    except TimeoutError:

        raise RuntimeError(
            "Ollama request timed out while "
            "processing the resume."
        )

    except Exception as error:

        raise RuntimeError(
            f"Ollama request failed: {error}"
        )

    # --------------------------------------------------------
    # Validate Ollama response
    # --------------------------------------------------------

    raw_response = result.get(
        "response",
        ""
    )

    if not raw_response:

        raise ValueError(
            "Ollama returned an empty response."
        )

    # --------------------------------------------------------
    # Convert LLM response into Python dictionary
    # --------------------------------------------------------

    try:

        parsed_response = json.loads(
            raw_response
        )

    except json.JSONDecodeError:

        print("\nRaw Ollama response:")
        print(raw_response)

        raise ValueError(
            "Ollama returned invalid JSON."
        )

    return parsed_response


# ============================================================
# RESUME UNDERSTANDING
# ============================================================

def understand_resume(resume_text: str) -> dict:

    if not resume_text.strip():

        raise ValueError(
            "Resume text is empty."
        )

    prompt = f"""
You are a Resume Understanding Agent working inside an
AI recruitment system.

Your task is to extract structured candidate information
from the resume provided below.

IMPORTANT RULES:

1. Extract information ONLY from the resume.
2. Do NOT invent information.
3. Do NOT assume missing skills.
4. Do NOT assume employment dates.
5. Do NOT calculate total years of experience.
6. Do NOT classify the candidate as Fresher, Junior,
   Mid-Level, or Senior.
7. Do NOT rank or evaluate the candidate.
8. Keep technologies exactly as supported by the resume.
9. Separate professional experience from personal/academic
   projects.
10. If information is unavailable:
    - use null for single values
    - use [] for lists
11. The candidate's name is normally located near the top of the
    resume and may appear without a "Name:" label.

12. Do not mistake section headings such as "Professional Summary",
    "Skills", "Education", "Experience", "Projects", or
    "Certifications" for the candidate's name.

13. Example:
    KARTHIK RAO
    Chennai, Tamil Nadu, India
    Email: karthik.rao@example.com

    The candidate name is "KARTHIK RAO".
14. For every professional employment entry, extract ALL
    responsibilities explicitly written under or associated with
    that employment entry.

15. For every professional employment entry, extract technologies
    ONLY when the resume explicitly associates those technologies
    with that employment entry.

16. Do NOT copy the candidate's general Skills section into an
    employment record unless the resume explicitly connects those
    skills to that employment.

17. Bullet points appearing directly below an employment heading
    belong to that employment entry until another section or
    employment entry begins.

18. Preserve meaningful responsibility text from the resume.
    Do not summarize away technical details.

19. If an employment entry has no documented responsibilities,
    return:
    "responsibilities": []

20. If an employment entry has no documented technologies,
    return:
    "technologies": []

21. Do not convert project technologies into professional
    employment technologies.

22. Do not infer that a technology was used at a company merely
    because it appears in the candidate's general Skills section.

23. Example:

    Resume text:

    IBM
    Associate System Engineer
    2024 - Present
    - Developed Python scripts for data processing.
    - Worked with SQL for database operations.
    - Used Pandas for data analysis.

    Correct extraction:

    {{
        "job_title": "Associate System Engineer",
        "company": "IBM",
        "start_date": "2024",
        "end_date": "Present",
        "responsibilities": [
            "Developed Python scripts for data processing.",
            "Worked with SQL for database operations.",
            "Used Pandas for data analysis."
        ],
        "technologies": [
            "Python",
            "SQL",
            "Pandas"
        ]
    }}

    However, only produce these responsibilities and technologies
    when they are actually supported by the resume being processed.

Return ONLY valid JSON.

Use exactly the following structure:

{{
    "name": null,
    "email": null,
    "phone": null,
    "location": null,

    "professional_summary": null,

    "skills": [],

    "education": [
        {{
            "degree": null,
            "field": null,
            "institution": null,
            "start_date": null,
            "end_date": null
        }}
    ],

    "experience": [
        {{
            "job_title": null,
            "company": null,
            "start_date": null,
            "end_date": null,
            "responsibilities": [],
            "technologies": []
        }}
    ],

    "projects": [
        {{
            "name": null,
            "description": null,
            "technologies": []
        }}
    ],

    "certifications": [
        {{
            "name": null,
            "issuer": null
        }}
    ]
}}

================ RESUME START ================

{resume_text}

================= RESUME END =================
"""

    print("\nPrompt prepared successfully.")
    print("Prompt characters:", len(prompt))

    candidate_profile = call_ollama(
        prompt
    )

    return candidate_profile




def extract_name_fallback(resume_text: str) -> str | None:
    """
    Extract a likely candidate name from the resume header
    when the LLM does not return a name.

    Only examines the first few non-empty lines and ignores
    common resume section headings.
    """

    if not resume_text:
        return None

    lines = [
        line.strip()
        for line in resume_text.splitlines()
        if line.strip()
    ]

    if not lines:
        return None

    # Common resume headings that must never be treated as names.
    excluded_headings = {
        "professional summary",
        "summary",
        "profile",
        "professional profile",
        "career objective",
        "objective",
        "skills",
        "technical skills",
        "key skills",
        "education",
        "experience",
        "professional experience",
        "work experience",
        "employment history",
        "projects",
        "academic projects",
        "personal projects",
        "certifications",
        "achievements",
        "contact",
        "contact information",
        "resume",
        "curriculum vitae",
    }

    # Only inspect the resume header.
    for line in lines[:6]:

        cleaned = line.strip()

        lower = cleaned.lower()

        # -----------------------------------------------
        # Ignore section headings
        # -----------------------------------------------

        if lower in excluded_headings:
            continue

        # -----------------------------------------------
        # Handle explicit "Name: Karthik Rao"
        # -----------------------------------------------

        if lower.startswith("name:"):

            name = cleaned.split(":", 1)[1].strip()

            if name:
                return name

        # -----------------------------------------------
        # Ignore contact information
        # -----------------------------------------------

        if "@" in cleaned:
            continue

        if lower.startswith(
            (
                "email:",
                "phone:",
                "mobile:",
                "location:",
                "address:",
                "linkedin:",
                "github:",
            )
        ):
            continue

        # URLs
        if "http://" in lower or "https://" in lower:
            continue

        if "linkedin.com" in lower:
            continue

        if "github.com" in lower:
            continue

        # Phone numbers / numeric-heavy lines
        if re.search(r"\d{5,}", cleaned):
            continue

        # -----------------------------------------------
        # Candidate name pattern
        # -----------------------------------------------

        if not re.fullmatch(
            r"[A-Za-z][A-Za-z .'-]{1,79}",
            cleaned,
        ):
            continue

        words = cleaned.split()

        # Most candidate names contain roughly 2-4 words.
        if not 2 <= len(words) <= 4:
            continue

        # Avoid long descriptive sentences.
        if len(cleaned) > 50:
            continue

        return cleaned.title()

    return None









# ============================================================
# VALIDATE CANDIDATE PROFILE
# ============================================================

def validate_candidate_profile(
    candidate_profile: dict
) -> dict:

    if not isinstance(
        candidate_profile,
        dict
    ):

        raise ValueError(
            "Candidate profile must be a JSON object."
        )

    # --------------------------------------------------------
    # Required top-level fields
    # --------------------------------------------------------

    required_fields = [
        "name",
        "email",
        "phone",
        "location",
        "professional_summary",
        "skills",
        "education",
        "experience",
        "projects",
        "certifications"
    ]

    # Add missing fields safely
    for field in required_fields:

        if field not in candidate_profile:

            if field in [
                "skills",
                "education",
                "experience",
                "projects",
                "certifications"
            ]:

                candidate_profile[field] = []

            else:

                candidate_profile[field] = None

    # --------------------------------------------------------
    # Make sure list fields are actually lists
    # --------------------------------------------------------

    list_fields = [
        "skills",
        "education",
        "experience",
        "projects",
        "certifications"
    ]

    for field in list_fields:

        if candidate_profile[field] is None:

            candidate_profile[field] = []

        elif not isinstance(
            candidate_profile[field],
            list
        ):

            candidate_profile[field] = [
                candidate_profile[field]
            ]

    return candidate_profile


# ============================================================
# COMPLETE RESUME PROCESSING
# ============================================================

def process_resume(file_path: str) -> dict:

    print("\n" + "=" * 70)
    print("RESUME UNDERSTANDING AGENT")
    print("=" * 70)

    print("\nResume file:")
    print(file_path)

    # --------------------------------------------------------
    # STEP 1: Parse resume
    # --------------------------------------------------------

    print("\n[1/4] Extracting resume text...")

    resume_text = parse_resume(
        file_path
    )

    print(
        "Resume characters:",
        len(resume_text)
    )

    print(
        "Resume words:",
        len(resume_text.split())
    )

    # --------------------------------------------------------
    # STEP 2: Send resume to LLM
    # --------------------------------------------------------

    print(
        "\n[2/4] Sending resume to "
        "Resume Understanding Agent..."
    )

    candidate_profile = understand_resume(
        resume_text
    )


    # --------------------------------------------------------
# NAME FALLBACK
# --------------------------------------------------------

    if not candidate_profile.get("name"):

        fallback_name = extract_name_fallback(
            resume_text
        )

        if fallback_name:

            candidate_profile["name"] = fallback_name

            print(
                "Candidate name recovered "
                f"from resume header: {fallback_name}"
            )

    # --------------------------------------------------------
    # STEP 3: Validate result
    # --------------------------------------------------------

    print(
        "\n[3/4] Validating candidate profile..."
    )

    candidate_profile = (
        validate_candidate_profile(
            candidate_profile
        )
    )

    # --------------------------------------------------------
    # STEP 4: Complete
    # --------------------------------------------------------

    print(
        "\n[4/4] Resume processing completed."
    )

    return candidate_profile
