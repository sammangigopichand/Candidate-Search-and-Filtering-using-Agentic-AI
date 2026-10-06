"""Entry point for the recruiter and interviewer dashboards."""

import streamlit as st


st.set_page_config(
    page_title="AI Recruitment System",
    page_icon=":material/groups:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize shared recruiter UI state in the entry point so it is present
# before Streamlit dispatches into the selected page.
for key, default in (
    ("raw_job_description", ""),
    ("extracted_job_profile", None),
    ("saved_job_id", None),
):
    st.session_state.setdefault(key, default)

pages = {
    "Workspace": [
        st.Page(
            "recruiter_ui.py",
            title="Recruiter dashboard",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(
            "interviewer_ui.py",
            title="Interviewer evaluation",
            icon=":material/rate_review:",
        ),
    ]
}

page = st.navigation(pages)
page.run()
