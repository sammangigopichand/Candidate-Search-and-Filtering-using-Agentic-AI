"""Coordinator Agent for the recruitment workflow.

The Coordinator Agent uses LangGraph to orchestrate the existing
specialized recruitment agents.

Automated workflow:

Resume Understanding
        ↓
Candidate Matching
        ↓
Experience Assessment
        ↓
Recruiter Review

LangGraph workflow checkpoints are persisted in PostgreSQL.

The coordinator does not make hiring decisions.
"""

import os
from contextlib import contextmanager
from typing import Any, TypedDict
from uuid import uuid4

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

from app.agents.resume_agent import process_resume
from app.agents.matching_agent import match_candidate
from app.agents.experience_agent import assess_experience


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# RECRUITMENT STATE
# ============================================================


class RecruitmentState(TypedDict, total=False):

    # --------------------------------------------------------
    # WORKFLOW IDENTIFICATION
    # --------------------------------------------------------

    workflow_id: str

    # --------------------------------------------------------
    # INPUTS
    # --------------------------------------------------------

    resume_path: str
    job_profile: dict[str, Any]

    # --------------------------------------------------------
    # AGENT OUTPUTS
    # --------------------------------------------------------

    candidate_profile: dict[str, Any]
    matching_report: dict[str, Any]
    experience_report: dict[str, Any]

    # --------------------------------------------------------
    # WORKFLOW STATE
    # --------------------------------------------------------

    current_stage: str
    workflow_status: str
    error: str | None


# ============================================================
# DATABASE URL
# ============================================================


def get_checkpoint_database_url() -> str:

    database_url = os.getenv(
        "DATABASE_URL"
    )

    if not database_url:

        raise RuntimeError(
            "DATABASE_URL is not configured in .env."
        )

    # --------------------------------------------------------
    # SQLALCHEMY URL → PSYCOPG URL
    # --------------------------------------------------------

    # Example:
    #
    # postgresql+psycopg://user:password@localhost/db
    #
    # becomes:
    #
    # postgresql://user:password@localhost/db

    database_url = database_url.replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )

    database_url = database_url.replace(
        "postgresql+psycopg2://",
        "postgresql://",
        1,
    )

    return database_url



# ============================================================
# LangGraph recruitment workflow checkpoints
# ============================================================



def clear_workflow_checkpoints() -> None:
    """
    Delete all LangGraph recruitment workflow checkpoints.

    Preserves checkpoint_migrations because LangGraph uses it
    for checkpoint schema management.
    """

    with checkpoint_context() as checkpointer:

        connection = checkpointer.conn

        with connection.cursor() as cursor:

            cursor.execute(
                "DELETE FROM checkpoint_writes"
            )

            cursor.execute(
                "DELETE FROM checkpoint_blobs"
            )

            cursor.execute(
                "DELETE FROM checkpoints"
            )

        connection.commit()


# ============================================================
# POSTGRES CHECKPOINTER
# ============================================================


@contextmanager
def checkpoint_context():

    database_url = (
        get_checkpoint_database_url()
    )

    with PostgresSaver.from_conn_string(
        database_url
    ) as checkpointer:

        yield checkpointer


# ============================================================
# RESUME UNDERSTANDING NODE
# ============================================================


def resume_understanding_node(
    state: RecruitmentState,
) -> dict[str, Any]:

    print(
        "\n[Coordinator] Resume Understanding Agent"
    )

    try:

        resume_path = state["resume_path"]

        candidate_profile = process_resume(
            resume_path
        )

        if not candidate_profile:

            raise ValueError(
                "Resume Understanding Agent returned "
                "an empty candidate profile."
            )

        return {
            "candidate_profile": candidate_profile,
            "current_stage": "resume_understanding",
            "workflow_status": "running",
            "error": None,
        }

    except Exception as exc:

        return {
            "current_stage": "resume_understanding",
            "workflow_status": "failed",
            "error": str(exc),
        }


# ============================================================
# MATCHING NODE
# ============================================================


def matching_node(
    state: RecruitmentState,
) -> dict[str, Any]:

    print(
        "\n[Coordinator] Candidate Matching Agent"
    )

    if state.get("error"):

        return {
            "current_stage": "matching",
            "workflow_status": "failed",
        }

    try:

        candidate_profile = state[
            "candidate_profile"
        ]

        job_profile = state[
            "job_profile"
        ]

        matching_report = match_candidate(
            candidate_profile,
            job_profile,
        )

        if not matching_report:

            raise ValueError(
                "Candidate Matching Agent returned "
                "an empty matching report."
            )

        return {
            "matching_report": matching_report,
            "current_stage": "matching",
            "workflow_status": "running",
            "error": None,
        }

    except Exception as exc:

        return {
            "current_stage": "matching",
            "workflow_status": "failed",
            "error": str(exc),
        }


# ============================================================
# EXPERIENCE NODE
# ============================================================


def experience_node(
    state: RecruitmentState,
) -> dict[str, Any]:

    print(
        "\n[Coordinator] Experience-Level Agent"
    )

    if state.get("error"):

        return {
            "current_stage": "experience_assessment",
            "workflow_status": "failed",
        }

    try:

        candidate_profile = state[
            "candidate_profile"
        ]

        job_profile = state[
            "job_profile"
        ]

        experience_report = assess_experience(
            candidate_profile,
            job_profile,
        )

        if not experience_report:

            raise ValueError(
                "Experience-Level Agent returned "
                "an empty experience report."
            )

        return {
            "experience_report": experience_report,
            "current_stage": "experience_assessment",
            "workflow_status": "running",
            "error": None,
        }

    except Exception as exc:

        return {
            "current_stage": "experience_assessment",
            "workflow_status": "failed",
            "error": str(exc),
        }


# ============================================================
# RECRUITER REVIEW NODE
# ============================================================


def recruiter_review_node(
    state: RecruitmentState,
) -> dict[str, Any]:

    print(
        "\n[Coordinator] Candidate ready "
        "for recruiter review"
    )

    if state.get("error"):

        return {
            "current_stage": "failed",
            "workflow_status": "failed",
        }

    return {
        "current_stage": "recruiter_review",
        "workflow_status": (
            "awaiting_recruiter_review"
        ),
        "error": None,
    }


# ============================================================
# ROUTING FUNCTIONS
# ============================================================


def route_after_resume(
    state: RecruitmentState,
) -> str:

    if state.get("error"):
        return "stop"

    return "continue"


def route_after_matching(
    state: RecruitmentState,
) -> str:

    if state.get("error"):
        return "stop"

    return "continue"


def route_after_experience(
    state: RecruitmentState,
) -> str:

    if state.get("error"):
        return "stop"

    return "continue"


# ============================================================
# BUILD LANGGRAPH
# ============================================================


def build_recruitment_graph(
    checkpointer,
):

    workflow = StateGraph(
        RecruitmentState
    )

    # --------------------------------------------------------
    # NODES
    # --------------------------------------------------------

    workflow.add_node(
        "resume_understanding",
        resume_understanding_node,
    )

    workflow.add_node(
        "candidate_matching",
        matching_node,
    )

    workflow.add_node(
        "experience_assessment",
        experience_node,
    )

    workflow.add_node(
        "recruiter_review",
        recruiter_review_node,
    )

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    workflow.add_conditional_edges(
        START,
        lambda state: "match_existing_profile"
        if state.get("candidate_profile")
        else "process_resume",
        {
            "match_existing_profile": "candidate_matching",
            "process_resume": "resume_understanding",
        },
    )

    # --------------------------------------------------------
    # RESUME → MATCHING
    # --------------------------------------------------------

    workflow.add_conditional_edges(
        "resume_understanding",
        route_after_resume,
        {
            "continue": "candidate_matching",
            "stop": END,
        },
    )

    # --------------------------------------------------------
    # MATCHING → EXPERIENCE
    # --------------------------------------------------------

    workflow.add_conditional_edges(
        "candidate_matching",
        route_after_matching,
        {
            "continue": "experience_assessment",
            "stop": END,
        },
    )

    # --------------------------------------------------------
    # EXPERIENCE → RECRUITER REVIEW
    # --------------------------------------------------------

    workflow.add_conditional_edges(
        "experience_assessment",
        route_after_experience,
        {
            "continue": "recruiter_review",
            "stop": END,
        },
    )

    # --------------------------------------------------------
    # HUMAN REVIEW BOUNDARY
    # --------------------------------------------------------

    workflow.add_edge(
        "recruiter_review",
        END,
    )

    return workflow.compile(
        checkpointer=checkpointer
    )


# ============================================================
# CREATE LANGGRAPH CONFIG
# ============================================================


def create_workflow_config(
    workflow_id: str,
) -> dict[str, Any]:

    return {
        "configurable": {
            "thread_id": workflow_id,
        }
    }


# ============================================================
# SETUP CHECKPOINT TABLES
# ============================================================


def setup_checkpoint_database() -> None:

    """
    Create the PostgreSQL tables required by LangGraph.

    This operation is safe to call multiple times.
    """

    with checkpoint_context() as checkpointer:

        checkpointer.setup()


# ============================================================
# PUBLIC COORDINATOR FUNCTION
# ============================================================


def process_candidate_workflow(
    resume_path: str,
    job_profile: dict[str, Any],
    workflow_id: str | None = None,
    candidate_profile: dict[str, Any] | None = None,
) -> RecruitmentState:

    """
    Execute the automated candidate-processing workflow.

    The workflow ends when the candidate is ready for
    recruiter review.

    LangGraph persists workflow checkpoints in PostgreSQL.

    The coordinator does NOT decide whether the candidate
    should proceed to interview.
    """

    if not resume_path:

        raise ValueError(
            "resume_path is required."
        )

    if not job_profile:

        raise ValueError(
            "job_profile is required."
        )

    if not workflow_id:

        workflow_id = str(
            uuid4()
        )

    initial_state: RecruitmentState = {
        "workflow_id": workflow_id,
        "resume_path": resume_path,
        "job_profile": job_profile,
        "current_stage": "started",
        "workflow_status": "running",
        "error": None,
    }
    if candidate_profile:
        initial_state["candidate_profile"] = candidate_profile

    config = create_workflow_config(
        workflow_id
    )

    with checkpoint_context() as checkpointer:

        graph = build_recruitment_graph(
            checkpointer
        )

        final_state = graph.invoke(
            initial_state,
            config=config,
        )

    return final_state


# ============================================================
# GET WORKFLOW STATE
# ============================================================


def get_workflow_state(
    workflow_id: str,
) -> RecruitmentState | None:

    """
    Retrieve the latest PostgreSQL-checkpointed workflow state.
    """

    if not workflow_id:
        return None

    config = create_workflow_config(
        workflow_id
    )

    with checkpoint_context() as checkpointer:

        graph = build_recruitment_graph(
            checkpointer
        )

        snapshot = graph.get_state(
            config
        )

        values = getattr(
            snapshot,
            "values",
            None,
        )

        if not values:
            return None

        return dict(values)


# ============================================================
# GET WORKFLOW HISTORY
# ============================================================


def get_workflow_history(
    workflow_id: str,
) -> list[RecruitmentState]:

    """
    Return PostgreSQL-checkpointed workflow history.
    """

    if not workflow_id:
        return []

    config = create_workflow_config(
        workflow_id
    )

    history: list[RecruitmentState] = []

    with checkpoint_context() as checkpointer:

        graph = build_recruitment_graph(
            checkpointer
        )

        for snapshot in graph.get_state_history(
            config
        ):

            values = getattr(
                snapshot,
                "values",
                None,
            )

            if values:

                history.append(
                    dict(values)
                )

    return history


# ============================================================
# WORKFLOW SUMMARY
# ============================================================


def get_workflow_summary(
    workflow_id: str,
) -> dict[str, Any] | None:

    """
    Return a compact workflow status representation.
    """

    state = get_workflow_state(
        workflow_id
    )

    if not state:
        return None

    return {
        "workflow_id": state.get(
            "workflow_id"
        ),
        "current_stage": state.get(
            "current_stage"
        ),
        "workflow_status": state.get(
            "workflow_status"
        ),
        "error": state.get(
            "error"
        ),
    }


# ============================================================
# DEVELOPMENT TEST
# ============================================================


if __name__ == "__main__":

    print(
        "Setting up LangGraph PostgreSQL "
        "checkpoint tables..."
    )

    setup_checkpoint_database()

    print(
        "Coordinator Agent loaded successfully."
    )

    print(
        "LangGraph checkpointing: PostgreSQL"
    )
