import re
from typing import Any


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_skill(skill: str) -> str:
    """
    Normalize skill names for consistent comparison.
    """

    if not isinstance(skill, str):
        return ""

    skill = skill.strip().lower()

    # Normalize different dash characters
    skill = (
        skill
        .replace("–", "-")
        .replace("—", "-")
    )

    # Remove unnecessary surrounding whitespace
    skill = re.sub(r"\s+", " ", skill)

    return skill


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {

    # Scikit-learn
    "scikit learn": "scikit-learn",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",

    # PyTorch
    "pytorch": "pytorch",
    "py torch": "pytorch",
    "torch": "pytorch",

    # PostgreSQL
    "postgres": "postgresql",
    "postgresql": "postgresql",

    # Machine Learning
    "ml": "machine learning",
    "machine learning": "machine learning",

    # Artificial Intelligence
    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",

    # JavaScript
    "javascript": "javascript",
    "java script": "javascript",
    "js": "javascript",

    # C++
    "c++": "c++",
    "cpp": "c++",

    # C#
    "c#": "c#",
    "c sharp": "c#",

    # Node
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",

    # TensorFlow
    "tensorflow": "tensorflow",
    "tensor flow": "tensorflow",

    # Keras
    "keras": "keras",

    # NumPy
    "numpy": "numpy",

    # Pandas
    "pandas": "pandas",

    # SQL
    "sql": "sql",
}


def canonical_skill(skill: str) -> str:
    """
    Convert a skill to its canonical representation.
    """

    normalized = normalize_skill(skill)

    return SKILL_ALIASES.get(
        normalized,
        normalized
    )


# ============================================================
# SPLIT GROUPED SKILL STRINGS
# ============================================================

def split_skill_string(skill_text: str) -> list[str]:
    """
    Convert grouped resume skill strings into individual skills.

    Example:

    "Programming Languages: Python, Java, C++, SQL"

    becomes:

    [
        "Python",
        "Java",
        "C++",
        "SQL"
    ]
    """

    if not isinstance(skill_text, str):
        return []

    skill_text = skill_text.strip()

    if not skill_text:
        return []

    # --------------------------------------------------------
    # Remove category prefix
    # --------------------------------------------------------
    #
    # Example:
    #
    # Programming Languages: Python, Java, SQL
    #
    # becomes:
    #
    # Python, Java, SQL
    #
    # --------------------------------------------------------

    if ":" in skill_text:

        _, skill_text = skill_text.split(
            ":",
            1
        )

    # --------------------------------------------------------
    # Normalize separators
    # --------------------------------------------------------

    skill_text = skill_text.replace(
        ";",
        ","
    )

    skill_text = re.sub(
        r"\s+\band\b\s+",
        ",",
        skill_text,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # Split individual skills
    # --------------------------------------------------------

    parts = skill_text.split(",")

    skills = []

    for part in parts:

        cleaned = part.strip()

        if cleaned:
            skills.append(cleaned)

    return skills


# ============================================================
# ADD SKILLS TO COLLECTION
# ============================================================

def add_skill_values(
    collected: list[str],
    value: Any
) -> None:
    """
    Add skill values safely.

    Supports:
    - strings
    - grouped strings
    - lists
    """

    if value is None:
        return

    # --------------------------------------------------------
    # Single string
    # --------------------------------------------------------

    if isinstance(value, str):

        collected.extend(
            split_skill_string(value)
        )

        return

    # --------------------------------------------------------
    # List / tuple / set
    # --------------------------------------------------------

    if isinstance(
        value,
        (list, tuple, set)
    ):

        for item in value:

            if isinstance(item, str):

                collected.extend(
                    split_skill_string(item)
                )


# ============================================================
# COLLECT DOCUMENTED CANDIDATE SKILLS
# ============================================================

def collect_candidate_skills(
    candidate_profile: dict
) -> list[str]:

    collected: list[str] = []

    # --------------------------------------------------------
    # 1. Explicit resume skills
    # --------------------------------------------------------

    add_skill_values(
        collected,
        candidate_profile.get("skills")
    )

    # --------------------------------------------------------
    # 2. Technologies used in projects
    # --------------------------------------------------------

    for project in (
        candidate_profile.get("projects")
        or []
    ):

        if not isinstance(project, dict):
            continue

        add_skill_values(
            collected,
            project.get("technologies")
        )

    # --------------------------------------------------------
    # 3. Technologies used in professional experience
    # --------------------------------------------------------

    for experience in (
        candidate_profile.get("experience")
        or []
    ):

        if not isinstance(experience, dict):
            continue

        add_skill_values(
            collected,
            experience.get("technologies")
        )

    # --------------------------------------------------------
    # 4. Remove duplicates using canonical names
    # --------------------------------------------------------

    unique_skills: dict[str, str] = {}

    for skill in collected:

        if not isinstance(skill, str):
            continue

        cleaned = skill.strip()

        if not cleaned:
            continue

        key = canonical_skill(cleaned)

        if (
            key
            and key not in unique_skills
        ):
            unique_skills[key] = cleaned

    return list(
        unique_skills.values()
    )


# ============================================================
# COMPARE SKILLS
# ============================================================

def compare_skills(
    required_skills: list[str],
    candidate_skills: list[str]
) -> dict:

    candidate_lookup = {}

    # --------------------------------------------------------
    # Build canonical candidate lookup
    # --------------------------------------------------------

    for skill in candidate_skills:

        key = canonical_skill(skill)

        if key:
            candidate_lookup[key] = skill

    matched = []
    missing = []

    # --------------------------------------------------------
    # Compare required skills
    # --------------------------------------------------------

    for required_skill in required_skills:

        if not isinstance(
            required_skill,
            str
        ):
            continue

        key = canonical_skill(
            required_skill
        )

        if key in candidate_lookup:

            matched.append({
                "required_skill":
                    required_skill,

                "candidate_skill":
                    candidate_lookup[key]
            })

        else:

            missing.append(
                required_skill
            )

    total = len(
        [
            skill
            for skill in required_skills
            if isinstance(skill, str)
            and skill.strip()
        ]
    )

    coverage = (
        round(
            len(matched)
            / total
            * 100,
            2
        )
        if total > 0
        else None
    )

    return {
        "matched": matched,
        "missing": missing,
        "total": total,
        "matched_count": len(matched),
        "coverage_percentage": coverage
    }


# ============================================================
# EXPERIENCE REQUIREMENTS
# ============================================================

def get_experience_requirements(
    job_profile: dict,
    candidate_profile: dict
) -> dict:

    return {

        "minimum_required_years":
            job_profile.get(
                "minimum_experience_years"
            ),

        "maximum_required_years":
            job_profile.get(
                "maximum_experience_years"
            ),

        "candidate_experience_records":
            candidate_profile.get(
                "experience"
            ) or [],

        "verification_status":
            "pending"
    }


# ============================================================
# EDUCATION REQUIREMENTS
# ============================================================

def get_education_requirements(
    job_profile: dict,
    candidate_profile: dict
) -> dict:

    return {

        "job_requirements":
            job_profile.get(
                "education"
            ) or [],

        "candidate_education":
            candidate_profile.get(
                "education"
            ) or [],

        "verification_status":
            "pending"
    }


# ============================================================
# CANDIDATE MATCHING AGENT
# ============================================================

def match_candidate(
    candidate_profile: dict,
    job_profile: dict,
    onet_results: list[dict] | None = None
) -> dict:

    if not isinstance(
        candidate_profile,
        dict
    ):
        raise ValueError(
            "Candidate profile must be a dictionary."
        )

    if not isinstance(
        job_profile,
        dict
    ):
        raise ValueError(
            "Job profile must be a dictionary."
        )

    # --------------------------------------------------------
    # STEP 1: Collect and normalize candidate skills
    # --------------------------------------------------------

    candidate_skills = (
        collect_candidate_skills(
            candidate_profile
        )
    )

    # --------------------------------------------------------
    # STEP 2: Compare required skills
    # --------------------------------------------------------

    required_match = compare_skills(
        job_profile.get(
            "required_skills"
        ) or [],
        candidate_skills
    )

    # --------------------------------------------------------
    # STEP 3: Compare preferred skills
    # --------------------------------------------------------

    preferred_match = compare_skills(
        job_profile.get(
            "preferred_skills"
        ) or [],
        candidate_skills
    )

    # --------------------------------------------------------
    # STEP 4: Extract relevant O*NET context
    # --------------------------------------------------------

    occupational_context = []

    for result in (
        onet_results or []
    ):

        if not isinstance(
            result,
            dict
        ):
            continue

        occupational_context.append({

            "occupation":
                result.get(
                    "occupation"
                ),

            "onet_soc_code":
                result.get(
                    "onet_soc_code"
                ),

            "document_type":
                result.get(
                    "document_type"
                ),

            "similarity_score":
                result.get(
                    "score"
                )
        })

    # --------------------------------------------------------
    # STEP 5: Prepare matching report
    # --------------------------------------------------------

    return {

        "candidate_name":
            candidate_profile.get(
                "name"
            ),

        "job_title":
            job_profile.get(
                "job_title"
            ),

        "candidate_skills":
            candidate_skills,

        "required_skills":
            required_match,

        "preferred_skills":
            preferred_match,

        "experience":
            get_experience_requirements(
                job_profile,
                candidate_profile
            ),

        "education":
            get_education_requirements(
                job_profile,
                candidate_profile
            ),

        "onet_context":
            occupational_context,

        "matching_status":
            "completed",

        "note": (
            "Skill coverage is based on explicitly documented "
            "skills and technologies after normalization. "
            "Experience and education verification are pending. "
            "O*NET similarity is occupational context and is "
            "not a candidate suitability score."
        )
    }