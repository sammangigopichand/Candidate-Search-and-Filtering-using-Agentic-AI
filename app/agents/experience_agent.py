import re
from datetime import date
from typing import Any

from app.agents.matching_agent import (
    canonical_skill,
    collect_candidate_skills,
)


# ============================================================
# PROJECT EXPERIENCE BANDS
# ============================================================

# These are project-defined bands.
# They are not universal industry standards.

EXPERIENCE_BANDS = [
    (0, "Fresher"),
    (2, "Junior"),
    (5, "Mid-Level"),
    (float("inf"), "Senior"),
]


# ============================================================
# DATE PARSING
# ============================================================

def parse_employment_date(
    value: Any,
    today: date,
):
    """
    Return earliest and latest possible dates represented
    by an employment date.

    Examples:

        2024
            -> 2024-01-01 through 2024-12-31

        2024-06
            -> 2024-06-01 through 2024-06-30

        2024-06-15
            -> exact date

        Present
            -> today's date

    Unknown or invalid values return None.
    """

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    normalized = text.lower()

    # --------------------------------------------------------
    # PRESENT / CURRENT
    # --------------------------------------------------------

    if normalized in {
        "present",
        "current",
        "ongoing",
        "till date",
        "till present",
    }:
        return today, today

    # --------------------------------------------------------
    # YEAR ONLY
    # --------------------------------------------------------

    if re.fullmatch(
        r"\d{4}",
        text,
    ):
        year = int(text)

        if not 1900 <= year <= today.year:
            return None

        earliest = date(
            year,
            1,
            1,
        )

        latest = min(
            date(
                year,
                12,
                31,
            ),
            today,
        )

        return earliest, latest

    # --------------------------------------------------------
    # YEAR-MONTH
    # --------------------------------------------------------

    if re.fullmatch(
        r"\d{4}-\d{2}",
        text,
    ):
        year, month = map(
            int,
            text.split("-"),
        )

        try:

            first_day = date(
                year,
                month,
                1,
            )

            if first_day > today:
                return None

            if month == 12:
                next_month = date(
                    year + 1,
                    1,
                    1,
                )
            else:
                next_month = date(
                    year,
                    month + 1,
                    1,
                )

            last_day = date.fromordinal(
                next_month.toordinal() - 1
            )

            return (
                first_day,
                min(
                    last_day,
                    today,
                ),
            )

        except ValueError:
            return None

    # --------------------------------------------------------
    # EXACT DATE
    # --------------------------------------------------------

    if re.fullmatch(
        r"\d{4}-\d{2}-\d{2}",
        text,
    ):
        try:

            parsed = date.fromisoformat(
                text
            )

            if parsed > today:
                return None

            return parsed, parsed

        except ValueError:
            return None

    return None


# ============================================================
# INTERVAL HELPERS
# ============================================================

def merge_intervals(intervals):
    """
    Merge overlapping employment intervals.

    This prevents simultaneous jobs from being
    counted twice.
    """

    if not intervals:
        return []

    intervals = sorted(
        intervals,
        key=lambda item: item[0],
    )

    merged = [
        intervals[0]
    ]

    for start, end in intervals[1:]:

        previous_start, previous_end = (
            merged[-1]
        )

        if start <= previous_end:

            merged[-1] = (
                previous_start,
                max(
                    previous_end,
                    end,
                ),
            )

        else:

            merged.append(
                (
                    start,
                    end,
                )
            )

    return merged


def interval_days(intervals):
    """
    Calculate the total number of documented
    days covered by employment intervals.
    """

    return sum(
        (end - start).days + 1
        for start, end
        in merge_intervals(intervals)
    )


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value: Any) -> str:
    """
    Normalize free text for evidence comparison.
    """

    if value is None:
        return ""

    text = str(value).lower()

    text = text.replace(
        "–",
        "-",
    )

    text = text.replace(
        "—",
        "-",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# ROLE TEXT EXTRACTION
# ============================================================

def build_role_text(
    experience: dict,
) -> str:
    """
    Build searchable text only from documented
    employment evidence.
    """

    values = []

    # --------------------------------------------------------
    # JOB TITLE
    # --------------------------------------------------------

    job_title = experience.get(
        "job_title"
    )

    if job_title:
        values.append(
            str(job_title)
        )

    # --------------------------------------------------------
    # COMPANY
    # --------------------------------------------------------

    company = experience.get(
        "company"
    )

    if company:
        values.append(
            str(company)
        )

    # --------------------------------------------------------
    # RESPONSIBILITIES
    # --------------------------------------------------------

    responsibilities = (
        experience.get(
            "responsibilities"
        )
        or []
    )

    if isinstance(
        responsibilities,
        str,
    ):
        values.append(
            responsibilities
        )

    elif isinstance(
        responsibilities,
        list,
    ):
        values.extend(
            str(item)
            for item in responsibilities
            if item
        )

    # --------------------------------------------------------
    # TECHNOLOGIES
    # --------------------------------------------------------

    technologies = (
        experience.get(
            "technologies"
        )
        or []
    )

    if isinstance(
        technologies,
        str,
    ):
        values.append(
            technologies
        )

    elif isinstance(
        technologies,
        list,
    ):
        values.extend(
            str(item)
            for item in technologies
            if item
        )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = experience.get(
        "description"
    )

    if description:
        values.append(
            str(description)
        )

    return normalize_text(
        " ".join(values)
    )


# ============================================================
# TITLE TOKENIZATION
# ============================================================

def title_tokens(title: str) -> set[str]:
    """
    Extract useful words from a job title.

    Example:

        Data Scientist

    becomes:

        {"data", "scientist"}
    """

    title = normalize_text(
        title
    )

    tokens = re.findall(
        r"[a-z0-9+#.-]+",
        title,
    )

    ignored = {
        "and",
        "or",
        "the",
        "a",
        "an",
        "of",
        "for",
        "to",
        "in",
    }

    return {
        token
        for token in tokens
        if token not in ignored
        and len(token) > 1
    }


# ============================================================
# DOCUMENTED ROLE SKILLS
# ============================================================

def collect_role_skills(
    experience: dict,
) -> list[str]:
    """
    Collect documented technologies/skills specifically
    from an employment record.
    """

    temporary_profile = {
        "skills": (
            experience.get(
                "technologies"
            )
            or []
        ),
        "projects": [],
        "experience": [],
    }

    return collect_candidate_skills(
        temporary_profile
    )


# ============================================================
# ROLE RELEVANCE
# ============================================================

def estimate_role_relevance(
    experience: dict,
    job_profile: dict,
):
    """
    Determine whether documented employment evidence
    overlaps with the target role.

    This is evidence matching, not a suitability score.

    Possible status:

        documented_overlap
        not_established
    """

    target_title = normalize_text(
        job_profile.get(
            "job_title"
        )
    )

    role_title = normalize_text(
        experience.get(
            "job_title"
        )
    )

    role_text = build_role_text(
        experience
    )

    evidence = []

    # ========================================================
    # 1. EXACT / PHRASE TITLE OVERLAP
    # ========================================================

    if (
        target_title
        and target_title in role_text
    ):

        evidence.append(
            f"Target job title documented: "
            f"{job_profile.get('job_title')}"
        )

    # ========================================================
    # 2. TITLE TOKEN OVERLAP
    # ========================================================

    target_tokens = title_tokens(
        target_title
    )

    role_tokens = title_tokens(
        role_title
    )

    shared_title_tokens = (
        target_tokens
        & role_tokens
    )

    if shared_title_tokens:

        evidence.append(
            "Job-title overlap: "
            + ", ".join(
                sorted(
                    shared_title_tokens
                )
            )
        )

    # ========================================================
    # 3. REQUIRED SKILL OVERLAP
    # ========================================================

    required_skills = (
        job_profile.get(
            "required_skills"
        )
        or []
    )

    role_skills = collect_role_skills(
        experience
    )

    role_skill_lookup = {
        canonical_skill(skill): skill
        for skill in role_skills
        if isinstance(skill, str)
    }

    for required_skill in required_skills:

        if not isinstance(
            required_skill,
            str,
        ):
            continue

        canonical_required = (
            canonical_skill(
                required_skill
            )
        )

        # First check structured technologies.
        if (
            canonical_required
            in role_skill_lookup
        ):

            evidence.append(
                "Required skill documented: "
                f"{required_skill}"
            )

            continue

        # Then check employment text.
        normalized_required = (
            normalize_text(
                required_skill
            )
        )

        if (
            normalized_required
            and normalized_required
            in role_text
        ):

            evidence.append(
                "Required skill documented "
                "in role evidence: "
                f"{required_skill}"
            )

    # ========================================================
    # REMOVE DUPLICATE EVIDENCE
    # ========================================================

    unique_evidence = []

    seen = set()

    for item in evidence:

        normalized = (
            item.strip().lower()
        )

        if normalized not in seen:

            seen.add(
                normalized
            )

            unique_evidence.append(
                item
            )

    return {
        "status": (
            "documented_overlap"
            if unique_evidence
            else "not_established"
        ),
        "evidence": unique_evidence,
    }


# ============================================================
# EXPERIENCE CLASSIFICATION
# ============================================================

def classify_experience(
    years: float,
):
    """
    Return a provisional classification using
    project-defined experience bands.
    """

    if years <= 0:
        return "Fresher"

    if years < 2:
        return "Junior"

    if years < 5:
        return "Mid-Level"

    return "Senior"


# ============================================================
# POSSIBLE LEVELS
# ============================================================

def determine_possible_levels(
    minimum_years: float,
    maximum_years: float,
):
    """
    Determine the range of possible levels when
    resume dates are imprecise.
    """

    minimum_level = classify_experience(
        minimum_years
    )

    maximum_level = classify_experience(
        maximum_years
    )

    if minimum_level == maximum_level:

        return (
            minimum_level,
            [minimum_level],
        )

    levels = [
        "Fresher",
        "Junior",
        "Mid-Level",
        "Senior",
    ]

    start_index = levels.index(
        minimum_level
    )

    end_index = levels.index(
        maximum_level
    )

    possible_levels = levels[
        start_index:end_index + 1
    ]

    return (
        "Undetermined",
        possible_levels,
    )


# ============================================================
# MAIN EXPERIENCE AGENT
# ============================================================

def assess_experience(
    candidate_profile: dict,
    job_profile: dict,
    reference_date=None,
):
    """
    Assess documented employment duration and
    documented role relevance.

    Important:

    - Academic projects are not counted as employment.
    - Missing employment dates are not invented.
    - Responsibilities absent from the resume are not inferred.
    - Role relevance requires documented evidence.
    """

    if not isinstance(
        candidate_profile,
        dict,
    ):
        raise ValueError(
            "Candidate profile must be a dictionary."
        )

    if not isinstance(
        job_profile,
        dict,
    ):
        raise ValueError(
            "Job profile must be a dictionary."
        )

    today = (
        reference_date
        or date.today()
    )

    experience_records = (
        candidate_profile.get(
            "experience"
        )
        or []
    )

    all_earliest_intervals = []
    all_latest_intervals = []

    relevant_earliest_intervals = []
    relevant_latest_intervals = []

    assessed_roles = []
    unverified_roles = []

    # ========================================================
    # PROCESS EACH EMPLOYMENT RECORD
    # ========================================================

    for record in experience_records:

        if not isinstance(
            record,
            dict,
        ):
            continue

        start_range = (
            parse_employment_date(
                record.get(
                    "start_date"
                ),
                today,
            )
        )

        end_range = (
            parse_employment_date(
                record.get(
                    "end_date"
                ),
                today,
            )
        )

        role_name = (
            record.get(
                "job_title"
            )
            or "Unknown role"
        )

        company = (
            record.get(
                "company"
            )
            or "Unknown company"
        )

        # ----------------------------------------------------
        # INVALID / MISSING DATES
        # ----------------------------------------------------

        if (
            start_range is None
            or end_range is None
        ):

            unverified_roles.append(
                {
                    "job_title":
                        role_name,

                    "company":
                        company,

                    "reason":
                        (
                            "Missing or unsupported "
                            "employment date"
                        ),
                }
            )

            continue

        earliest_start, latest_start = (
            start_range
        )

        earliest_end, latest_end = (
            end_range
        )

        if earliest_start > latest_end:

            unverified_roles.append(
                {
                    "job_title":
                        role_name,

                    "company":
                        company,

                    "reason":
                        (
                            "Start date is after "
                            "end date"
                        ),
                }
            )

            continue

        # ----------------------------------------------------
        # DURATION RANGE
        # ----------------------------------------------------

        # Minimum possible duration:
        # latest possible start -> earliest possible end

        minimum_start = (
            latest_start
        )

        minimum_end = max(
            latest_start,
            earliest_end,
        )

        earliest_interval = (
            minimum_start,
            minimum_end,
        )

        # Maximum possible duration:
        # earliest possible start -> latest possible end

        latest_interval = (
            earliest_start,
            latest_end,
        )

        # ----------------------------------------------------
        # ROLE RELEVANCE
        # ----------------------------------------------------

        relevance = (
            estimate_role_relevance(
                record,
                job_profile,
            )
        )

        all_earliest_intervals.append(
            earliest_interval
        )

        all_latest_intervals.append(
            latest_interval
        )

        if (
            relevance["status"]
            == "documented_overlap"
        ):

            relevant_earliest_intervals.append(
                earliest_interval
            )

            relevant_latest_intervals.append(
                latest_interval
            )

        assessed_roles.append(
            {
                "job_title":
                    role_name,

                "company":
                    company,

                "start_date":
                    record.get(
                        "start_date"
                    ),

                "end_date":
                    record.get(
                        "end_date"
                    ),

                "relevance":
                    relevance,
            }
        )

    # ========================================================
    # TOTAL EXPERIENCE
    # ========================================================

    minimum_years = round(
        interval_days(
            all_earliest_intervals
        )
        / 365.25,
        2,
    )

    maximum_years = round(
        interval_days(
            all_latest_intervals
        )
        / 365.25,
        2,
    )

    # ========================================================
    # DOCUMENTED RELEVANT EXPERIENCE
    # ========================================================

    relevant_minimum_years = round(
        interval_days(
            relevant_earliest_intervals
        )
        / 365.25,
        2,
    )

    relevant_maximum_years = round(
        interval_days(
            relevant_latest_intervals
        )
        / 365.25,
        2,
    )

    # ========================================================
    # EXPERIENCE LEVEL
    # ========================================================

    level, possible_levels = (
        determine_possible_levels(
            minimum_years,
            maximum_years,
        )
    )

    # ========================================================
    # JOB EXPERIENCE REQUIREMENT
    # ========================================================

    minimum_required = (
        job_profile.get(
            "minimum_experience_years"
        )
    )

    maximum_required = (
        job_profile.get(
            "maximum_experience_years"
        )
    )

    experience_requirement_status = (
        "not_specified"
    )

    if minimum_required is not None:

        try:

            minimum_required = float(
                minimum_required
            )

            if (
                relevant_minimum_years
                >= minimum_required
            ):

                experience_requirement_status = (
                    "documented_meets_minimum"
                )

            elif (
                relevant_maximum_years
                >= minimum_required
            ):

                experience_requirement_status = (
                    "possible_but_not_verified"
                )

            else:

                experience_requirement_status = (
                    "documented_below_minimum"
                )

        except (
            TypeError,
            ValueError,
        ):

            experience_requirement_status = (
                "invalid_job_requirement"
            )

    # ========================================================
    # RESULT
    # ========================================================

    return {

        "candidate_name":
            candidate_profile.get(
                "name"
            ),

        "target_job":
            job_profile.get(
                "job_title"
            ),

        "reference_date":
            today.isoformat(),

        "total_experience_years": {
            "minimum":
                minimum_years,

            "maximum":
                maximum_years,
        },

        "documented_relevant_experience_years": {
            "minimum":
                relevant_minimum_years,

            "maximum":
                relevant_maximum_years,
        },

        "provisional_experience_level":
            level,

        "possible_experience_levels":
            possible_levels,

        "job_experience_requirement": {

            "minimum_required_years":
                minimum_required,

            "maximum_required_years":
                maximum_required,

            "status":
                experience_requirement_status,
        },

        "assessed_roles":
            assessed_roles,

        "unverified_roles":
            unverified_roles,

        "note": (
            "Experience is estimated only from documented "
            "employment dates. Role relevance requires "
            "documented overlap with the target role or "
            "required skills. Academic projects are not "
            "counted as employment. Imprecise dates may "
            "produce a range of possible experience levels. "
            "Human verification is required."
        ),
    }