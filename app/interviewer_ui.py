"""
Run with:
python -m streamlit run app/interviewer_ui.py
"""


from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.auth_store import (
    authenticate_user,
    auth_database_session,
)

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
from sqlalchemy import select


# ============================================================
# PROJECT IMPORT PATH
# ============================================================

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)


# ============================================================
# PROJECT IMPORTS
# ============================================================

from app.agents.evaluation_agent import (
    OPTIONS,
    evaluate_interview,
)

from app.interview_store import (
    InterviewSession,
    database_session,
    get_interview,
    interview_data,
    saved_selections,
    save_progress,
    submit_evaluation,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================


# ============================================================
# AUTHENTICATION
# ============================================================

def interviewer_login():

    st.title("AI Recruitment System")
    st.subheader("Interviewer Login")

    with st.form("interviewer_login_form"):

        login = st.text_input(
            "Username or Email"
        )

        password = st.text_input(
            "Password",
            type="password",
        )

        submitted = st.form_submit_button(
            "Login",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        if not login.strip() or not password:

            st.error(
                "Enter username/email and password."
            )

            return

        AuthSessionLocal = auth_database_session()
        auth_db = AuthSessionLocal()

        try:

            user = authenticate_user(
                auth_db,
                login,
                password,
            )

            if user is None:

                st.error(
                    "Invalid username/email or password."
                )

                return

            if user.role != "interviewer":

                st.error(
                    "This account does not have interviewer access."
                )

                return

            st.session_state["authenticated"] = True
            st.session_state["auth_user_id"] = user.id
            st.session_state["auth_username"] = user.username
            st.session_state["auth_full_name"] = user.full_name
            st.session_state["auth_role"] = user.role

            st.rerun()

        finally:

            auth_db.close()


def interviewer_logout():

    auth_keys = [
        "authenticated",
        "auth_user_id",
        "auth_username",
        "auth_full_name",
        "auth_role",
        "active_interview",
        "loaded_interview",
        "selections",
        "question_index",
        "review",
        "started_interview",
        "started_for",
    ]

    for key in auth_keys:

        st.session_state.pop(
            key,
            None,
        )

    st.rerun()


# ============================================================
# REQUIRE INTERVIEWER AUTHENTICATION
# ============================================================

if not st.session_state.get(
    "authenticated",
    False,
):

    interviewer_login()
    st.stop()


if st.session_state.get(
    "auth_role"
) != "interviewer":

    st.error(
        "You are not authorized to access the interviewer dashboard."
    )

    if st.button("Logout"):

        interviewer_logout()

    st.stop()


# ============================================================
# AUTHENTICATED INTERVIEWER
# ============================================================

interviewer_id = st.session_state[
    "auth_user_id"
]


with st.sidebar:

    st.markdown("### AI Recruitment")

    st.divider()

    st.write(
        f"**{st.session_state.get('auth_full_name', 'Interviewer')}**"
    )

    st.caption("Interviewer")

    username = st.session_state.get(
        "auth_username"
    )

    if username:

        st.caption(
            f"@{username}"
        )

    st.caption(
        f"ID: {interviewer_id}"
    )

    st.divider()

    if st.button(
        "Logout",
        use_container_width=True,
        key="interviewer_logout",
    ):

        interviewer_logout()


st.title("Interview evaluation", icon=":material/rate_review:")

st.caption(
    "Assess the candidate against a consistent checklist, save progress, "
    "and submit the completed evaluation."
)


# ============================================================
# HELPER: FORMAT SCORE
# ============================================================

def format_score(score):

    if score is None:
        return "Not Assessed"

    if isinstance(score, str):

        if score.lower() == "not assessed":
            return "Not Assessed"

        try:
            score = float(score)

        except ValueError:
            return score

    try:
        return f"{float(score):.2f}%"

    except (TypeError, ValueError):
        return str(score)


# ============================================================
# HELPER: SELECTION ICON
# ============================================================

def selection_icon(option):

    icons = {
        "Yes": "✓",
        "Partially": "◐",
        "No": "✗",
        "Not Assessed": "—",
    }

    return icons.get(option, "?")


# ============================================================
# SESSION HEADER
# ============================================================

def render_session_header(
    data,
    interviewer_id,
    status,
    candidate_summary,
):

    st.subheader(
        f"{data['target_job']} - "
        f"{data['interview_round']}"
    )

    candidate_name = (
        candidate_summary.get("name")
        or "Unknown Candidate"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Candidate",
        candidate_name,
    )

    col2.metric(
        "Interviewer",
        interviewer_id,
    )

    col3.metric(
        "Status",
        (
            "Pending"
            if status == "draft"
            else status.title()
        ),
    )

    interview_date = str(
        data.get(
            "interview_date",
            "",
        )
    )

    if "T" in interview_date:
        interview_date = interview_date.split("T")[0]

    col4.metric(
        "Interview Date",
        interview_date or "N/A",
    )


# ============================================================
# CANDIDATE INFORMATION
# ============================================================

def render_candidate_summary(summary):

    with st.expander(
        "Candidate Professional Information",
        expanded=False,
    ):

        if not summary:

            st.info(
                "No candidate professional information "
                "is available."
            )

            return

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        name = summary.get("name")

        if name:
            st.markdown(f"### {name}")

        # ----------------------------------------------------
        # EXPERIENCE LEVEL
        # ----------------------------------------------------

        experience_level = (
            summary.get("experience_level")
        )

        if experience_level:

            st.markdown(
                "**Experience Level**"
            )

            st.write(
                experience_level
            )

        # ----------------------------------------------------
        # SKILLS
        # ----------------------------------------------------

        skills = (
            summary.get("skills")
            or []
        )

        if skills:

            st.markdown(
                "**Skills**"
            )

            st.write(
                ", ".join(
                    map(str, skills)
                )
            )

        # ----------------------------------------------------
        # EXPERIENCE
        # ----------------------------------------------------

        experience = (
            summary.get("experience")
            or []
        )

        if experience:

            st.markdown(
                "**Experience**"
            )

            for item in experience:

                if isinstance(item, dict):

                    job_title = (
                        item.get("job_title")
                        or item.get("role")
                        or item.get("title")
                        or "Experience"
                    )

                    company = (
                        item.get("company")
                        or ""
                    )

                    if company:

                        st.write(
                            f"• {job_title} - {company}"
                        )

                    else:

                        st.write(
                            f"• {job_title}"
                        )

                else:

                    st.write(
                        f"• {item}"
                    )

        # ----------------------------------------------------
        # PROJECTS
        # ----------------------------------------------------

        projects = (
            summary.get("projects")
            or []
        )

        if projects:

            st.markdown(
                "**Projects**"
            )

            for project in projects:

                if isinstance(project, dict):

                    title = (
                        project.get("name")
                        or project.get("title")
                        or "Project"
                    )

                    st.markdown(
                        f"- **{title}**"
                    )

                    description = (
                        project.get("description")
                    )

                    if description:

                        st.write(
                            description
                        )

                    technologies = (
                        project.get("technologies")
                        or []
                    )

                    if technologies:

                        st.caption(
                            "Technologies: "
                            + ", ".join(
                                map(
                                    str,
                                    technologies,
                                )
                            )
                        )

                else:

                    st.write(
                        f"• {project}"
                    )

        # ----------------------------------------------------
        # EDUCATION
        # ----------------------------------------------------

        education = (
            summary.get("education")
            or []
        )

        if education:

            st.markdown(
                "**Education**"
            )

            for item in education:

                if isinstance(item, dict):

                    degree = (
                        item.get("degree")
                        or item.get("qualification")
                        or ""
                    )

                    field = (
                        item.get("field")
                        or ""
                    )

                    institution = (
                        item.get("institution")
                        or ""
                    )

                    parts = [
                        value
                        for value in [
                            degree,
                            field,
                            institution,
                        ]
                        if value
                    ]

                    if parts:

                        st.write(
                            "• "
                            + " - ".join(parts)
                        )

                else:

                    st.write(
                        f"• {item}"
                    )


# ============================================================
# SCORE SUMMARY
# ============================================================

def render_score_summary(report):

    st.markdown(
        "## Evaluation Summary"
    )

    overall = report.get(
        "overall_score",
        "Not Assessed",
    )

    technical = report.get(
        "technical_score",
        "Not Assessed",
    )

    project = report.get(
        "project_score",
        "Not Assessed",
    )

    behavioral = report.get(
        "behavioral_score",
        "Not Assessed",
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Overall Score",
        format_score(overall),
    )

    col2.metric(
        "Technical",
        format_score(technical),
    )

    col3.metric(
        "Project",
        format_score(project),
    )

    col4.metric(
        "Behavioral",
        format_score(behavioral),
    )


# ============================================================
# QUESTION RESULTS
# ============================================================

def render_question_results(report):

    st.markdown(
        "## Question Results"
    )

    question_results = (
        report.get("question_results")
        or report.get("questions")
        or []
    )

    if not question_results:

        st.info(
            "No question-level results available."
        )

        return

    for position, result in enumerate(
        question_results,
        start=1,
    ):

        question_id = result.get(
            "question_id",
            position,
        )

        category = str(
            result.get(
                "category",
                "",
            )
        ).title()

        difficulty = str(
            result.get(
                "difficulty",
                "",
            )
        ).title()

        score = format_score(
            result.get("score")
        )

        title = (
            f"Question {question_id} | "
            f"{category} | "
            f"Score: {score}"
        )

        with st.expander(
            title,
            expanded=False,
        ):

            question_text = (
                result.get(
                    "question",
                    "Question unavailable",
                )
            )

            st.markdown(
                f"### {question_text}"
            )

            if difficulty:

                st.caption(
                    f"Difficulty: {difficulty}"
                )

            criteria = (
                result.get(
                    "criteria",
                    [],
                )
            )

            if criteria:

                st.markdown(
                    "**Interviewer Checklist**"
                )

            for criterion in criteria:

                option = (
                    criterion.get(
                        "selected_option"
                    )
                )

                criterion_text = (
                    criterion.get(
                        "criterion",
                        "",
                    )
                )

                icon = selection_icon(
                    option
                )

                st.markdown(
                    f"{icon} "
                    f"**{criterion_text}**"
                )

                st.caption(
                    "Assessment: "
                    f"{option or 'Unselected'}"
                )


# ============================================================
# EVIDENCE SECTION
# ============================================================

def render_evidence_section(
    title,
    items,
    empty_message,
):

    st.markdown(
        f"### {title}"
    )

    if not items:

        st.caption(
            empty_message
        )

        return

    for item in items:

        if isinstance(item, dict):

            criterion = (
                item.get(
                    "criterion",
                    str(item),
                )
            )

            question_id = (
                item.get(
                    "question_id"
                )
            )

            if question_id:

                st.markdown(
                    f"- **Q{question_id}:** "
                    f"{criterion}"
                )

            else:

                st.markdown(
                    f"- {criterion}"
                )

        else:

            st.markdown(
                f"- {item}"
            )


# ============================================================
# FINAL REPORT
# ============================================================

def render_final_report(report):

    if not report:

        st.warning(
            "The submitted session does not "
            "contain an evaluation report."
        )

        return

    st.success(
        "Evaluation submitted successfully."
    )

    render_score_summary(
        report
    )

    st.divider()

    render_question_results(
        report
    )

    st.divider()

    st.markdown(
        "## Assessment Evidence"
    )

    col1, col2 = st.columns(2)

    with col1:

        render_evidence_section(
            "Strengths",
            report.get(
                "observed_strengths",
                [],
            ),
            (
                "No criteria were recorded "
                "as fully met."
            ),
        )

        render_evidence_section(
            "Partially Demonstrated",
            report.get(
                "partially_met",
                [],
            ),
            (
                "No criteria were recorded "
                "as partially met."
            ),
        )

    with col2:

        render_evidence_section(
            "Areas Requiring Improvement",
            report.get(
                "areas_requiring_improvement",
                [],
            ),
            (
                "No criteria were recorded "
                "as not met."
            ),
        )

        render_evidence_section(
            "Not Assessed",
            report.get(
                "unassessed_criteria",
                [],
            ),
            (
                "All recorded criteria "
                "were assessed."
            ),
        )

    st.divider()

    st.markdown(
        "### Score Basis"
    )

    score_basis = report.get(
        "score_basis",
        (
            "Scores reflect interviewer checklist "
            "assessments. The system does not make "
            "the final hiring decision."
        ),
    )

    st.info(
        score_basis
    )

    with st.expander(
        "Raw Evaluation Data"
    ):

        st.json(
            report
        )


# ============================================================
# INTERVIEW PROGRESS
# ============================================================

def render_progress(
    questions,
    selections,
    current_index,
):

    total_questions = len(
        questions
    )

    question_progress = (
        (current_index + 1)
        / total_questions
        if total_questions
        else 0
    )

    st.progress(
        question_progress,
        text=(
            f"Question "
            f"{current_index + 1} "
            f"of {total_questions}"
        ),
    )

    all_criteria = [
        criterion
        for question in questions
        for criterion in question[
            "evaluation_criteria"
        ]
    ]

    total_criteria = len(
        all_criteria
    )

    completed = sum(
        1
        for criterion in all_criteria
        if selections.get(
            criterion[
                "criterion_id"
            ]
        )
        is not None
    )

    st.caption(
        f"{completed} / "
        f"{total_criteria} "
        "checklist criteria evaluated"
    )


# ============================================================
# REVIEW SCREEN
# ============================================================

def render_review_screen(
    Session,
    session_id,
    interviewer_id,
    data,
    questions,
    selections,
):

    st.markdown(
        "## Interview Review"
    )

    st.caption(
        "Review all checklist selections before "
        "submitting the final evaluation."
    )

    missing = []

    for question in questions:

        question_id = (
            question[
                "question_id"
            ]
        )

        category = (
            question[
                "category"
            ].title()
        )

        difficulty = (
            question[
                "difficulty"
            ].title()
        )

        with st.expander(
            (
                f"Question {question_id} | "
                f"{category} | "
                f"{difficulty}"
            ),
            expanded=False,
        ):

            st.markdown(
                f"### {question['question']}"
            )

            for criterion in question[
                "evaluation_criteria"
            ]:

                criterion_id = (
                    criterion[
                        "criterion_id"
                    ]
                )

                option = (
                    selections.get(
                        criterion_id
                    )
                )

                icon = (
                    selection_icon(
                        option
                    )
                )

                st.markdown(
                    f"{icon} "
                    f"**{criterion['criterion']}**"
                )

                if option:

                    st.caption(
                        f"Assessment: {option}"
                    )

                else:

                    st.caption(
                        "Assessment: Unselected"
                    )

                    missing.append(
                        criterion_id
                    )

    st.divider()

    # --------------------------------------------------------
    # MISSING CRITERIA
    # --------------------------------------------------------

    if missing:

        st.warning(
            "Every criterion must have an explicit "
            "selection before final submission. "
            "'Not Assessed' is a valid selection."
        )

        st.write(
            "Unanswered criteria: "
            + ", ".join(
                missing
            )
        )

    # --------------------------------------------------------
    # PREVIEW
    # --------------------------------------------------------

    else:

        preview = (
            evaluate_interview(
                data,
                selections,
            )
        )

        st.markdown(
            "### Evaluation Preview"
        )

        render_score_summary(
            preview
        )

    # --------------------------------------------------------
    # REVIEW BUTTONS
    # --------------------------------------------------------

    left, right = st.columns(2)

    if left.button(
        "Back to Interview",
        use_container_width=True,
    ):

        st.session_state[
            "review"
        ] = False

        st.rerun()

    if right.button(
        "Submit Final Evaluation",
        type="primary",
        disabled=bool(missing),
        use_container_width=True,
    ):

        try:

            with Session() as db:

                submit_evaluation(
                    db,
                    session_id,
                    interviewer_id,
                    selections,
                )

            st.session_state[
                "review"
            ] = False

            st.session_state[
                "started_interview"
            ] = False

            st.session_state[
                "started_for"
            ] = None

            st.rerun()

        except Exception as exc:

            st.error(
                f"Submission failed: {exc}"
            )


# ============================================================
# DATABASE CONNECTION
# ============================================================

try:

    Session = (
        database_session()
    )

except Exception as exc:

    st.error(
        f"Database unavailable: {exc}"
    )

    st.stop()


# # ============================================================
# # INTERVIEWER IDENTIFICATION
# # ============================================================

# st.divider()

# st.subheader(
#     "Interviewer Access"
# )

# interviewer_id = (
#     st.text_input(
#         "Interviewer ID",
#         value="INT001",
#         key="interviewer_id",
#     ).strip()
# )


# if not interviewer_id:

#     st.info(
#         "Enter your interviewer ID to load "
#         "your assigned interview sessions."
#     )

#     st.stop()


# ============================================================
# LOAD ASSIGNED INTERVIEWS
# ============================================================

try:

    with Session() as db:

        records = db.scalars(

            select(
                InterviewSession
            )

            .options(
                selectinload(InterviewSession.report)
            )

            .where(
                InterviewSession.interviewer_id
                == interviewer_id
            )

            .order_by(
                InterviewSession
                .interview_date
                .desc()
            )

        ).all()


except Exception as exc:

    st.error(
        "Unable to load assigned interviews: "
        f"{exc}"
    )

    st.stop()


# ============================================================
# NO INTERVIEWS
# ============================================================

if not records:

    st.info(
        "No interview sessions are currently "
        "assigned to this interviewer."
    )

    st.stop()


# ============================================================
# SPLIT PENDING / COMPLETED
# ============================================================

draft_records = [
    record
    for record in records
    if record.status == "draft"
]

submitted_records = [
    record
    for record in records
    if record.status == "submitted"
]

if draft_records:
    st.info(
        f"🔔 You have {len(draft_records)} pending interview assignment(s). "
        "Open a session below to review the candidate and interview details."
    )

with st.sidebar:
    st.divider()
    st.markdown("#### Interview queue")
    queue_col1, queue_col2 = st.columns(2)
    queue_col1.metric("Pending", len(draft_records))
    queue_col2.metric("Completed", len(submitted_records))
    sidebar_status_filter = st.selectbox(
        "Show sessions",
        ["Pending", "Completed", "All"],
        key="interview_sidebar_status_filter",
    )
    sidebar_candidate_search = st.text_input(
        "Find a candidate",
        placeholder="Search by name",
        key="interview_sidebar_candidate_search",
    )


# ============================================================
# INTERVIEWER DASHBOARD
# ============================================================

st.divider()

st.subheader(
    "Assigned Interviews"
)

col1, col2, col3 = (
    st.columns(3)
)

col1.metric(
    "Total Assigned",
    len(records),
)

col2.metric(
    "Pending",
    len(draft_records),
)

col3.metric(
    "Completed",
    len(submitted_records),
)

st.subheader("Past Interviews")
if submitted_records:
    past_interview_rows = []
    for record in submitted_records:
        summary = record.candidate_summary or {}
        report = record.report.data if record.report else {}
        past_interview_rows.append({
            "Candidate": summary.get("name") or "Unknown Candidate",
            "Job": record.target_job,
            "Round": record.interview_round,
            "Interview Date": record.interview_date.strftime("%Y-%m-%d") if record.interview_date else "",
            "Overall Score": report.get("overall_score", "Not assessed"),
            "Session": record.id[:8],
        })
    st.dataframe(
        pd.DataFrame(past_interview_rows),
        hide_index=True,
        width="stretch",
    )
else:
    st.caption("Completed interviews will appear here after you submit an evaluation.")

# ============================================================
# STATUS FILTER
# ============================================================

if sidebar_status_filter == "Pending":

    filtered_records = (
        draft_records
    )

elif sidebar_status_filter == "Completed":

    filtered_records = (
        submitted_records
    )

else:

    filtered_records = (
        records
    )


if not filtered_records:

    st.info(
        f"No {sidebar_status_filter.lower()} "
        "interviews are available."
    )

    st.stop()


# ============================================================
# CREATE READABLE SESSION LABELS
# ============================================================

choices = {}


for record in filtered_records:

    candidate_summary = (
        record.candidate_summary
        or {}
    )

    candidate_name = (
        candidate_summary.get(
            "name"
        )
        or "Unknown Candidate"
    )

    search_term = sidebar_candidate_search.strip().casefold()
    if search_term and search_term not in candidate_name.casefold():
        continue

    if record.status == "draft":

        status_label = (
            "Pending"
        )

    else:

        status_label = (
            "Completed"
        )

    label = (
        f"{candidate_name} | "
        f"{record.target_job} | "
        f"{record.interview_round} | "
        f"{status_label}"
    )

    # Prevent duplicate dictionary keys.
    if label in choices:

        label = (
            f"{label} | "
            f"{record.id[:8]}"
        )

    choices[
        label
    ] = record.id

if not choices:
    st.info("No assigned interviews match the sidebar filters.")
    st.stop()


# ============================================================
# INTERVIEW SELECTOR
# ============================================================

st.divider()

st.subheader(
    "Interview Sessions"
)

ids = list(
    choices.values()
)

active = (
    st.session_state.get(
        "active_interview"
    )
)


selected_label = st.selectbox(
    "Select Interview",
    list(choices.keys()),
    index=(
        ids.index(active)
        if active in ids
        else 0
    ),
)


session_id = (
    choices[
        selected_label
    ]
)


st.session_state[
    "active_interview"
] = session_id


# ============================================================
# LOAD SESSION STATE WHEN INTERVIEW CHANGES
# ============================================================

if (
    st.session_state.get(
        "loaded_interview"
    )
    != session_id
):

    try:

        with Session() as db:

            record = (
                get_interview(
                    db,
                    session_id,
                    interviewer_id,
                )
            )

            st.session_state[
                "selections"
            ] = saved_selections(
                record
            )

    except Exception as exc:

        st.error(
            "Unable to load interview: "
            f"{exc}"
        )

        st.stop()

    st.session_state[
        "loaded_interview"
    ] = session_id

    st.session_state[
        "question_index"
    ] = 0

    st.session_state[
        "review"
    ] = False

    st.session_state[
        "started_interview"
    ] = False

    st.session_state[
        "started_for"
    ] = None


# ============================================================
# LOAD INTERVIEW DATA
# ============================================================

try:

    with Session() as db:

        record = (
            get_interview(
                db,
                session_id,
                interviewer_id,
            )
        )

        data = (
            interview_data(
                record
            )
        )

        summary = (
            record.candidate_summary
            or {}
        )

        status = (
            record.status
        )

        final_report = (
            record.report.data
            if record.report
            else None
        )

except Exception as exc:

    st.error(
        "Unable to load interview details: "
        f"{exc}"
    )

    st.stop()


active_questions = data.get("questions", [])
active_selections = st.session_state.get("selections", {})
active_criteria = [
    criterion
    for question in active_questions
    for criterion in question.get("evaluation_criteria", [])
]
assessed_criteria_count = sum(
    active_selections.get(criterion.get("criterion_id")) is not None
    for criterion in active_criteria
)

with st.sidebar:
    st.divider()
    st.markdown("#### Selected interview")
    st.markdown(f"**{summary.get('name') or 'Unknown Candidate'}**")
    st.caption(f"{data.get('target_job', 'Role not specified')} · {data.get('interview_round', 'Round not specified')}")
    st.badge(
        "Completed" if status == "submitted" else "In progress" if assessed_criteria_count else "Not started",
        color="green" if status == "submitted" else "blue" if assessed_criteria_count else "orange",
    )
    if status != "submitted":
        st.progress(
            assessed_criteria_count / len(active_criteria) if active_criteria else 0,
            text=f"Checklist · {assessed_criteria_count}/{len(active_criteria)} assessed",
        )


# ============================================================
# SESSION INFORMATION
# ============================================================

st.divider()

render_session_header(
    data,
    interviewer_id,
    status,
    summary,
)

render_candidate_summary(
    summary
)


# ============================================================
# COMPLETED / SUBMITTED INTERVIEW
# ============================================================

if status == "submitted":

    st.divider()

    render_final_report(
        final_report
    )

    st.stop()


# ============================================================
# START INTERVIEW SCREEN
# ============================================================

if (
    not st.session_state.get(
        "started_interview"
    )
    or
    st.session_state.get(
        "started_for"
    )
    != session_id
):

    st.divider()

    st.info(
        "This interview session is ready."
    )

    candidate_name = (
        summary.get(
            "name"
        )
        or "Unknown Candidate"
    )

    info_col, button_col = (
        st.columns(
            [3, 1]
        )
    )

    with info_col:

        st.write(
            "**Candidate:**",
            candidate_name,
        )

        st.write(
            "**Position:**",
            data.get(
                "target_job",
                "N/A",
            ),
        )

        st.write(
            "**Interview Round:**",
            data.get(
                "interview_round",
                "N/A",
            ),
        )

        st.write(
            "**Interviewer:**",
            interviewer_id,
        )

    with button_col:

        if st.button(
            "Start Interview",
            type="primary",
            use_container_width=True,
        ):

            st.session_state[
                "started_interview"
            ] = True

            st.session_state[
                "started_for"
            ] = session_id

            st.session_state[
                "question_index"
            ] = 0

            st.session_state[
                "review"
            ] = False

            st.rerun()

    st.stop()


# ============================================================
# ACTIVE INTERVIEW
# ============================================================

questions = (
    data.get(
        "questions",
        [],
    )
)

selections = (
    st.session_state.get(
        "selections",
        {},
    )
)


# ============================================================
# VALIDATE QUESTIONS
# ============================================================

if not questions:

    st.error(
        "This interview session contains "
        "no interview questions."
    )

    st.stop()


# ============================================================
# REVIEW SCREEN
# ============================================================

if st.session_state.get(
    "review",
    False,
):

    render_review_screen(
        Session=Session,
        session_id=session_id,
        interviewer_id=interviewer_id,
        data=data,
        questions=questions,
        selections=selections,
    )

    st.stop()


# ============================================================
# QUESTION INDEX
# ============================================================

index = (
    st.session_state.get(
        "question_index",
        0,
    )
)


if index < 0:

    index = 0


if index >= len(questions):

    index = (
        len(questions) - 1
    )


st.session_state[
    "question_index"
] = index


# ============================================================
# CURRENT QUESTION
# ============================================================

question = (
    questions[
        index
    ]
)


# ============================================================
# PROGRESS
# ============================================================

render_progress(
    questions,
    selections,
    index,
)


st.divider()


# ============================================================
# QUESTION INFORMATION
# ============================================================

category = str(
    question.get(
        "category",
        "",
    )
).title()


difficulty = str(
    question.get(
        "difficulty",
        "",
    )
).title()


st.caption(
    f"{category} | "
    f"{difficulty}"
)


st.markdown(
    f"## Question {index + 1}"
)


st.markdown(
    f"### {question['question']}"
)


# ============================================================
# EXPECTED CONCEPTS
# ============================================================

with st.expander(
    "Expected Concepts"
):

    expected_concepts = (
        question.get(
            "expected_concepts",
            [],
        )
    )

    if expected_concepts:

        for concept in expected_concepts:

            st.markdown(
                f"- {concept}"
            )

    else:

        st.caption(
            "No expected concepts provided."
        )


# ============================================================
# EVALUATION CHECKLIST
# ============================================================

st.divider()

st.markdown(
    "### Evaluation Checklist"
)

st.caption(
    "Select exactly one assessment "
    "for each criterion."
)


for criterion in question[
    "evaluation_criteria"
]:

    criterion_id = (
        criterion[
            "criterion_id"
        ]
    )

    current = (
        selections.get(
            criterion_id
        )
    )

    choices_for_criterion = [
        "Select an option",
        *OPTIONS,
    ]

    if (
        current
        in choices_for_criterion
    ):

        current_index = (
            choices_for_criterion.index(
                current
            )
        )

    else:

        current_index = 0


    selected = st.radio(
        criterion[
            "criterion"
        ],
        choices_for_criterion,
        index=current_index,
        key=(
            f"{session_id}_"
            f"{criterion_id}"
        ),
        horizontal=True,
    )


    if (
        selected
        == "Select an option"
    ):

        selections.pop(
            criterion_id,
            None,
        )

    else:

        selections[
            criterion_id
        ] = selected


# Keep selections in Streamlit state.
st.session_state[
    "selections"
] = selections


# ============================================================
# NAVIGATION
# ============================================================

st.divider()


previous_col, save_col, next_col = (
    st.columns(3)
)


# ============================================================
# PREVIOUS QUESTION
# ============================================================

if previous_col.button(
    "Previous Question",
    disabled=(
        index == 0
    ),
    use_container_width=True,
):

    st.session_state[
        "question_index"
    ] -= 1

    st.rerun()


# ============================================================
# SAVE DRAFT
# ============================================================

if save_col.button(
    "Save Draft",
    use_container_width=True,
):

    try:

        with Session() as db:

            save_progress(
                db,
                session_id,
                interviewer_id,
                selections,
            )

        st.success(
            "Interview progress saved."
        )

    except Exception as exc:

        st.error(
            "Unable to save draft: "
            f"{exc}"
        )


# ============================================================
# NEXT QUESTION
# ============================================================

if index < len(questions) - 1:

    if next_col.button(
        "Next Question",
        type="primary",
        use_container_width=True,
    ):

        st.session_state[
            "question_index"
        ] += 1

        st.rerun()


# ============================================================
# LAST QUESTION -> REVIEW
# ============================================================

else:

    if next_col.button(
        "Review Evaluation",
        type="primary",
        use_container_width=True,
    ):

        st.session_state[
            "review"
        ] = True

        st.rerun()


# ============================================================
# OPTIONAL EARLY REVIEW
# ============================================================

if index < len(questions) - 1:

    if st.button(
        "Review Current Evaluation",
        use_container_width=True,
    ):

        st.session_state[
            "review"
        ] = True

        st.rerun()
