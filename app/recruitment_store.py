"""PostgreSQL persistence for recruitment data."""

import hashlib
import tempfile
import os

from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    select,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)


load_dotenv()


# ============================================================
# DATABASE BASE
# ============================================================


class RecruitmentBase(DeclarativeBase):
    pass


# ============================================================
# JOB
# ============================================================


class Job(RecruitmentBase):

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    job_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    raw_job_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    job_profile: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


# ============================================================
# CANDIDATE
# ============================================================


class Candidate(RecruitmentBase):

    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    resume_filename: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # SHA-256 hash of the original uploaded resume.
    #
    # Existing database rows may contain NULL because they were
    # created before duplicate-resume protection was introduced.
    resume_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    candidate_profile: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


# ============================================================
# CANDIDATE ↔ JOB MATCH
# ============================================================


class CandidateJobMatch(RecruitmentBase):

    __tablename__ = "candidate_job_matches"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False,
    )

    job_id: Mapped[str] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    matching_report: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    experience_report: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    workflow_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "job_id",
            name="uq_candidate_job_match",
        ),
    )


# ============================================================
# DATABASE SESSION
# ============================================================


def recruitment_database_session():

    database_url = os.getenv("DATABASE_URL")

    if not database_url:

        raise RuntimeError(
            "Set DATABASE_URL to a PostgreSQL SQLAlchemy URL."
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    RecruitmentBase.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


# ============================================================
# CREATE JOB
# ============================================================


def create_job(
    db,
    raw_job_description: str,
    job_profile: dict,
):

    job_title = (
        job_profile.get("job_title")
        or "Untitled Job"
    )

    record = Job(
        id=str(uuid4()),
        job_title=job_title,
        raw_job_description=raw_job_description,
        job_profile=job_profile,
        status="active",
        created_at=datetime.now(timezone.utc),
    )

    db.add(record)
    db.commit()

    return record.id


# ============================================================
# CREATE CANDIDATE
# ============================================================


def create_candidate(
    db,
    candidate_profile: dict,
    resume_filename: str | None = None,
    resume_hash: str | None = None,
):

    candidate_name = (
        candidate_profile.get("name")
        or "Unknown Candidate"
    )

    record = Candidate(
        id=str(uuid4()),
        name=candidate_name,
        resume_filename=resume_filename,
        resume_hash=resume_hash,
        candidate_profile=candidate_profile,
        created_at=datetime.now(timezone.utc),
    )

    db.add(record)
    db.commit()

    return record.id


# ============================================================
# FIND CANDIDATE BY RESUME HASH
# ============================================================


def get_candidate_by_resume_hash(
    db,
    resume_hash: str | None,
):
    """
    Find an existing candidate using the SHA-256 hash of the
    uploaded resume.

    Candidate name is deliberately not used for duplicate
    detection because multiple people can have the same name.

    Existing candidates created before resume hashing may have
    resume_hash=NULL and therefore cannot be identified by this
    function until they are uploaded again and associated with
    a hash.
    """

    if not resume_hash:
        return None

    normalized_hash = str(resume_hash).strip().lower()

    if not normalized_hash:
        return None

    return db.scalar(
        select(Candidate).where(
            Candidate.resume_hash == normalized_hash
        )
    )


# ============================================================
# GET OR CREATE CANDIDATE
# ============================================================


def get_or_create_candidate(
    db,
    candidate_profile: dict,
    resume_filename: str | None = None,
    resume_hash: str | None = None,
):
    """
    Get an existing candidate when the same resume has already
    been uploaded, otherwise create a new candidate.

    Returns:

        {
            "candidate_id": "...",
            "created": True/False,
            "reused": True/False
        }

    When an existing candidate is found, the latest structured
    candidate profile is stored so that improvements to the
    Resume Understanding Agent can be reflected without creating
    another candidate record.
    """

    normalized_hash = None

    if resume_hash:

        normalized_hash = (
            str(resume_hash)
            .strip()
            .lower()
        )

        if not normalized_hash:
            normalized_hash = None

    # --------------------------------------------------------
    # LOOK FOR EXISTING CANDIDATE
    # --------------------------------------------------------

    existing = get_candidate_by_resume_hash(
        db,
        normalized_hash,
    )

    if existing:

        candidate_name = (
            candidate_profile.get("name")
            or existing.name
            or "Unknown Candidate"
        )

        existing.name = candidate_name

        existing.candidate_profile = candidate_profile

        if resume_filename:
            existing.resume_filename = resume_filename

        db.commit()

        return {
            "candidate_id": existing.id,
            "created": False,
            "reused": True,
        }

    # --------------------------------------------------------
    # CREATE NEW CANDIDATE
    # --------------------------------------------------------

    candidate_id = create_candidate(
        db,
        candidate_profile=candidate_profile,
        resume_filename=resume_filename,
        resume_hash=normalized_hash,
    )

    return {
        "candidate_id": candidate_id,
        "created": True,
        "reused": False,
    }


# ============================================================
# SAVE MATCH
# ============================================================


def save_candidate_match(
    db,
    candidate_id: str,
    job_id: str,
    matching_report: dict,
    experience_report: dict,
    workflow_id: str | None = None,
):

    existing = db.scalar(
        select(CandidateJobMatch).where(
            CandidateJobMatch.candidate_id
            == candidate_id,
            CandidateJobMatch.job_id
            == job_id,
        )
    )

    # --------------------------------------------------------
    # UPDATE EXISTING CANDIDATE/JOB MATCH
    # --------------------------------------------------------

    if existing:

        existing.matching_report = matching_report
        existing.experience_report = experience_report

        if workflow_id:
            existing.workflow_id = workflow_id

        existing.created_at = datetime.now(
            timezone.utc
        )

        db.commit()

        return existing.id

    # --------------------------------------------------------
    # CREATE NEW CANDIDATE/JOB MATCH
    # --------------------------------------------------------

    record = CandidateJobMatch(
        id=str(uuid4()),
        candidate_id=candidate_id,
        job_id=job_id,
        matching_report=matching_report,
        experience_report=experience_report,
        workflow_id=workflow_id,
        created_at=datetime.now(
            timezone.utc
        ),
    )

    db.add(record)
    db.commit()

    return record.id

# ============================================================
# GET JOB
# ============================================================


def get_job(
    db,
    job_id: str,
):

    record = db.get(
        Job,
        job_id,
    )

    if record is None:

        raise ValueError(
            "Job not found."
        )

    return record


# ============================================================
# GET CANDIDATE
# ============================================================


def get_candidate(
    db,
    candidate_id: str,
):

    record = db.get(
        Candidate,
        candidate_id,
    )

    if record is None:

        raise ValueError(
            "Candidate not found."
        )

    return record


# ============================================================
# LIST ACTIVE JOBS
# ============================================================


def list_active_jobs(db):

    return list(
        db.scalars(
            select(Job)
            .where(
                Job.status == "active"
            )
            .order_by(
                Job.created_at.desc()
            )
        )
    )


# ============================================================
# LIST CANDIDATES
# ============================================================


def list_candidates(db):

    return list(
        db.scalars(
            select(Candidate)
            .order_by(
                Candidate.created_at.desc()
            )
        )
    )


# ============================================================
# GET MATCHES FOR JOB
# ============================================================


def get_matches_for_job(
    db,
    job_id: str,
):

    return list(
        db.scalars(
            select(CandidateJobMatch)
            .where(
                CandidateJobMatch.job_id
                == job_id
            )
            .order_by(
                CandidateJobMatch.created_at.desc()
            )
        )
    )


# ============================================================
# GET CANDIDATE + MATCH RECORDS FOR JOB
# ============================================================


def get_candidate_matches_for_job(
    db,
    job_id: str,
):
    """
    Return every candidate match for a selected job.

    No relevance filtering is applied here.

    This function is used when the recruiter explicitly
    requests the All Candidates view.
    """

    statement = (
        select(
            CandidateJobMatch,
            Candidate,
        )
        .join(
            Candidate,
            Candidate.id
            == CandidateJobMatch.candidate_id,
        )
        .where(
            CandidateJobMatch.job_id
            == job_id
        )
        .order_by(
            CandidateJobMatch.created_at.desc()
        )
    )

    return list(
        db.execute(statement).all()
    )


# ============================================================
# MATCHING REPORT HELPERS
# ============================================================


def get_skill_coverage(
    matching_report: dict | None,
) -> float:
    """
    Safely extract required-skill coverage.

    Current project structure:

    {
        "required_skills": {
            "coverage_percentage": 83.33,
            "matched": [...],
            "missing": [...]
        }
    }

    Older top-level structures are also supported.
    """

    if not isinstance(
        matching_report,
        dict,
    ):
        return 0.0

    # --------------------------------------------------------
    # CURRENT PROJECT STRUCTURE
    # --------------------------------------------------------

    required_skills = matching_report.get(
        "required_skills"
    )

    if isinstance(required_skills, dict):

        value = required_skills.get(
            "coverage_percentage"
        )

        if value is not None:

            try:
                return float(value)

            except (
                TypeError,
                ValueError,
            ):
                pass

    # --------------------------------------------------------
    # FALLBACK STRUCTURES
    # --------------------------------------------------------

    possible_fields = (
        "required_skill_coverage_percentage",
        "coverage_percentage",
        "coverage",
        "skill_coverage",
    )

    for field in possible_fields:

        value = matching_report.get(field)

        if value is None:
            continue

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            continue

    return 0.0


def get_matched_skills(
    matching_report: dict | None,
) -> list:
    """
    Return matched required skills.

    Supports both the current nested Matching Agent report and
    older top-level structures.
    """

    if not isinstance(
        matching_report,
        dict,
    ):
        return []

    # --------------------------------------------------------
    # CURRENT PROJECT STRUCTURE
    # --------------------------------------------------------

    required_skills = matching_report.get(
        "required_skills"
    )

    if isinstance(required_skills, dict):

        values = required_skills.get(
            "matched"
        )

        if isinstance(values, list):
            return values

    # --------------------------------------------------------
    # FALLBACK STRUCTURES
    # --------------------------------------------------------

    values = (
        matching_report.get(
            "matched_required_skills"
        )
        or matching_report.get(
            "matched_skills"
        )
        or []
    )

    if not isinstance(values, list):
        return []

    return values


def get_missing_skills(
    matching_report: dict | None,
) -> list:
    """
    Return missing required skills.

    Supports both the current nested Matching Agent report and
    older top-level structures.
    """

    if not isinstance(
        matching_report,
        dict,
    ):
        return []

    # --------------------------------------------------------
    # CURRENT PROJECT STRUCTURE
    # --------------------------------------------------------

    required_skills = matching_report.get(
        "required_skills"
    )

    if isinstance(required_skills, dict):

        values = required_skills.get(
            "missing"
        )

        if isinstance(values, list):
            return values

    # --------------------------------------------------------
    # FALLBACK STRUCTURES
    # --------------------------------------------------------

    values = (
        matching_report.get(
            "missing_required_skills"
        )
        or matching_report.get(
            "missing_skills"
        )
        or []
    )

    if not isinstance(values, list):
        return []

    return values


# ============================================================
# EXPERIENCE REPORT HELPERS
# ============================================================


def get_relevant_experience_range(
    experience_report: dict | None,
) -> dict:
    """
    Return the documented job-relevant professional
    experience range.

    Projects are not treated as professional employment.
    """

    if not isinstance(
        experience_report,
        dict,
    ):

        return {
            "minimum": 0.0,
            "maximum": 0.0,
        }

    relevant = (
        experience_report.get(
            "documented_relevant_experience_years"
        )
        or experience_report.get(
            "relevant_experience_years"
        )
        or {}
    )

    if not isinstance(
        relevant,
        dict,
    ):

        return {
            "minimum": 0.0,
            "maximum": 0.0,
        }

    try:

        minimum = float(
            relevant.get(
                "minimum",
                0.0,
            )
            or 0.0
        )

    except (
        TypeError,
        ValueError,
    ):

        minimum = 0.0

    try:

        maximum = float(
            relevant.get(
                "maximum",
                0.0,
            )
            or 0.0
        )

    except (
        TypeError,
        ValueError,
    ):

        maximum = 0.0

    return {
        "minimum": minimum,
        "maximum": maximum,
    }


def has_documented_relevant_experience(
    experience_report: dict | None,
) -> bool:
    """
    Return True when the Experience Agent established some
    documented job-relevant professional experience.
    """

    relevant = get_relevant_experience_range(
        experience_report
    )

    return (
        relevant.get(
            "maximum",
            0.0,
        )
        > 0.0
    )


# ============================================================
# RELEVANCE FILTER
# ============================================================


def candidate_passes_relevance_filter(
    matching_report: dict | None,
    experience_report: dict | None,
    minimum_skill_coverage: float = 60.0,
    require_relevant_experience: bool = False,
    maximum_missing_required_skills: int | None = None,
) -> bool:
    """
    Apply transparent recruiter-controlled relevance rules.

    This function controls candidate presentation only.

    It does NOT make the hiring decision and does NOT delete or
    reject candidates.

    Rules:

    1. Required-skill coverage must reach the configured
       threshold.

    2. If relevant experience is required, documented relevant
       professional experience must exist.

    3. If a maximum number of missing skills is configured, the
       candidate cannot exceed that number.

    Recruiters can still use the All Candidates view.
    """

    # --------------------------------------------------------
    # NORMALIZE COVERAGE THRESHOLD
    # --------------------------------------------------------

    try:

        minimum_skill_coverage = float(
            minimum_skill_coverage
        )

    except (
        TypeError,
        ValueError,
    ):

        minimum_skill_coverage = 60.0

    minimum_skill_coverage = max(
        0.0,
        min(
            minimum_skill_coverage,
            100.0,
        ),
    )

    # --------------------------------------------------------
    # SKILL COVERAGE
    # --------------------------------------------------------

    coverage = get_skill_coverage(
        matching_report
    )

    if coverage < minimum_skill_coverage:
        return False

    # --------------------------------------------------------
    # RELEVANT PROFESSIONAL EXPERIENCE
    # --------------------------------------------------------

    if require_relevant_experience:

        if not has_documented_relevant_experience(
            experience_report
        ):

            return False

    # --------------------------------------------------------
    # MISSING REQUIRED SKILLS
    # --------------------------------------------------------

    if (
        maximum_missing_required_skills
        is not None
    ):

        try:

            maximum_missing_required_skills = int(
                maximum_missing_required_skills
            )

        except (
            TypeError,
            ValueError,
        ):

            maximum_missing_required_skills = None

        if (
            maximum_missing_required_skills
            is not None
        ):

            maximum_missing_required_skills = max(
                0,
                maximum_missing_required_skills,
            )

            missing_skills = get_missing_skills(
                matching_report
            )

            if (
                len(missing_skills)
                > maximum_missing_required_skills
            ):

                return False

    return True


# ============================================================
# GET RELEVANT CANDIDATES FOR JOB
# ============================================================


def get_relevant_candidate_matches_for_job(
    db,
    job_id: str,
    minimum_skill_coverage: float = 60.0,
    require_relevant_experience: bool = False,
    maximum_missing_required_skills: int | None = None,
):
    """
    Return candidates satisfying the current recruiter-selected
    relevance filters.

    All candidates remain stored in PostgreSQL.
    """

    all_rows = get_candidate_matches_for_job(
        db,
        job_id,
    )

    relevant_rows = []

    for match_record, candidate in all_rows:

        if candidate_passes_relevance_filter(
            matching_report=(
                match_record.matching_report
            ),
            experience_report=(
                match_record.experience_report
            ),
            minimum_skill_coverage=(
                minimum_skill_coverage
            ),
            require_relevant_experience=(
                require_relevant_experience
            ),
            maximum_missing_required_skills=(
                maximum_missing_required_skills
            ),
        ):

            relevant_rows.append(
                (
                    match_record,
                    candidate,
                )
            )

    return relevant_rows


# ============================================================
# GET CANDIDATE VIEW FOR JOB
# ============================================================


def get_candidate_view_for_job(
    db,
    job_id: str,
    view: str = "relevant",
    minimum_skill_coverage: float = 60.0,
    require_relevant_experience: bool = False,
    maximum_missing_required_skills: int | None = None,
):
    """
    Single entry point for candidate retrieval.

    view="relevant"
        Apply recruiter-controlled relevance filtering.

    view="all"
        Return every processed candidate for the job.

    This controls presentation only.
    """

    normalized_view = (
        str(view)
        .strip()
        .lower()
    )

    if normalized_view == "all":

        return get_candidate_matches_for_job(
            db,
            job_id,
        )

    return get_relevant_candidate_matches_for_job(
        db=db,
        job_id=job_id,
        minimum_skill_coverage=(
            minimum_skill_coverage
        ),
        require_relevant_experience=(
            require_relevant_experience
        ),
        maximum_missing_required_skills=(
            maximum_missing_required_skills
        ),
    )


# ============================================================
# CANDIDATE VIEW COUNTS
# ============================================================


def get_candidate_view_counts(
    db,
    job_id: str,
    minimum_skill_coverage: float = 60.0,
    require_relevant_experience: bool = False,
    maximum_missing_required_skills: int | None = None,
):
    """
    Return counts for the recruiter dashboard.

    Example:

    {
        "all": 24,
        "relevant": 7,
        "hidden_by_current_filter": 17
    }
    """

    all_rows = get_candidate_matches_for_job(
        db,
        job_id,
    )

    relevant_rows = (
        get_relevant_candidate_matches_for_job(
            db=db,
            job_id=job_id,
            minimum_skill_coverage=(
                minimum_skill_coverage
            ),
            require_relevant_experience=(
                require_relevant_experience
            ),
            maximum_missing_required_skills=(
                maximum_missing_required_skills
            ),
        )
    )

    all_count = len(
        all_rows
    )

    relevant_count = len(
        relevant_rows
    )

    return {
        "all": all_count,
        "relevant": relevant_count,
        "hidden_by_current_filter": (
            all_count
            - relevant_count
        ),
    }


def clear_candidate_recruitment_data(db):
    """
    Delete candidate-related recruitment data.

    This removes:
    - Candidate/job matches
    - Candidates

    Saved jobs are preserved.

    Interview/evaluation data must be deleted first because
    those records may reference candidates.
    """

    db.query(CandidateJobMatch).delete(
        synchronize_session=False
    )

    db.query(Candidate).delete(
        synchronize_session=False
    )

    db.commit()