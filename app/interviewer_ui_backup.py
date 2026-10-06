"""Run with: streamlit run app/interviewer_ui.py"""

import json
import sys
from pathlib import Path

import streamlit as st
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.evaluation_agent import OPTIONS, evaluate_interview
from app.agents.experience_agent import assess_experience
from app.agents.interview_agent import generate_interview_questions
from app.interview_store import InterviewSession, create_interview, database_session, get_interview, interview_data, saved_selections, save_progress, submit_evaluation


st.set_page_config(page_title="Interviewer Evaluation", layout="wide")
st.title("Interviewer evaluation")
st.caption("Face-to-face interview checklist. Scores reflect the interviewer's selections.")

try:
    Session = database_session()
except Exception as exc:
    st.error(f"Database unavailable: {exc}")
    st.stop()

interviewer_id = st.text_input("Interviewer ID", key="interviewer_id").strip()
if not interviewer_id:
    st.info("Enter your interviewer ID to load your sessions.")
    st.stop()

with Session() as db:
    records = db.scalars(select(InterviewSession).where(InterviewSession.interviewer_id == interviewer_id).order_by(InterviewSession.interview_date.desc())).all()
    choices = {f"{r.candidate_id} · {r.target_job} · {r.interview_round} · {r.status} · {r.id[:8]}": r.id for r in records}

with st.expander("Create interview session"):
    st.caption("Paste candidate and job profile JSON from the existing agent outputs.")
    candidate_id = st.text_input("Candidate ID")
    job_id = st.text_input("Job ID")
    interview_round = st.text_input("Interview round", value="Round 1")
    candidate_json = st.text_area("Candidate profile JSON")
    job_json = st.text_area("Job profile JSON")
    if st.button("Generate questions and create session"):
        try:
            if not candidate_id or not job_id or not candidate_json or not job_json:
                raise ValueError("Candidate ID, job ID, and both profiles are required.")
            candidate = json.loads(candidate_json)
            job = json.loads(job_json)
            experience = assess_experience(candidate_profile=candidate, job_profile=job)
            generated = generate_interview_questions(candidate, job, experience)
            summary = {key: candidate.get(key) for key in ("name", "skills", "experience", "projects", "education")}
            with Session() as db:
                session_id = create_interview(db, candidate_id=candidate_id, job_id=job_id, interviewer_id=interviewer_id, target_job=generated["target_job"] or job_id, interview_round=interview_round, candidate_summary=summary, questions=generated["questions"])
            st.session_state.active_interview = session_id
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

if not choices:
    st.info("No interview sessions yet. Create one above.")
    st.stop()

ids = list(choices.values())
active = st.session_state.get("active_interview")
selected_label = st.selectbox("Interview session", list(choices), index=ids.index(active) if active in ids else 0)
session_id = choices[selected_label]
if st.session_state.get("loaded_interview") != session_id:
    with Session() as db:
        record = get_interview(db, session_id, interviewer_id)
        st.session_state.selections = saved_selections(record)
    st.session_state.loaded_interview = session_id
    st.session_state.question_index = 0
    st.session_state.review = False

with Session() as db:
    record = get_interview(db, session_id, interviewer_id)
    data = interview_data(record)
    summary = record.candidate_summary
    status = record.status
    final_report = record.report.data if record.report else None

st.subheader(f"{data['target_job']} · {data['interview_round']}")
st.write(f"Candidate: {data['candidate_id']} | Interviewer: {interviewer_id} | Date: {data['interview_date']} | Status: {status}")
with st.expander("Candidate professional information"):
    st.json(summary)

if status == "submitted":
    st.subheader("Final evaluation report")
    st.json(final_report)
    st.stop()

if not st.session_state.get("started_interview") or st.session_state.get("started_for") != session_id:
    if st.button("Start interview"):
        st.session_state.started_interview = True
        st.session_state.started_for = session_id
        st.rerun()
    st.stop()

questions = data["questions"]
selections = st.session_state.selections
if st.session_state.review:
    st.subheader("Review selections")
    missing = []
    for question in questions:
        st.markdown(f"**Question {question['question_id']}: {question['question']}**")
        for criterion in question["evaluation_criteria"]:
            key = criterion["criterion_id"]
            option = selections.get(key)
            st.write(f"{criterion['criterion']} — {option or 'Unselected'}")
            if option is None:
                missing.append(key)
    if missing:
        st.warning(f"Select an option for every criterion before submitting: {', '.join(missing)}")
    else:
        preview = evaluate_interview(data, selections)
        st.write("Overall checklist score:", preview["overall_score"])
        if st.button("Submit evaluation", type="primary"):
            try:
                with Session() as db:
                    submit_evaluation(db, session_id, interviewer_id, selections)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    if st.button("Back to questions"):
        st.session_state.review = False
        st.rerun()
    st.stop()

index = st.session_state.question_index
question = questions[index]
st.progress((index + 1) / len(questions), text=f"Question {index + 1} of {len(questions)}")
st.subheader(question["question"])
st.write(f"Category: {question['category']} | Difficulty: {question['difficulty']}")
st.write("Expected concepts:", ", ".join(question["expected_concepts"]))
st.markdown("**Evaluation checklist**")
for criterion in question["evaluation_criteria"]:
    key = criterion["criterion_id"]
    choices_for_criterion = ["Select an option", *OPTIONS]
    current = selections.get(key)
    selected = st.radio(criterion["criterion"], choices_for_criterion, index=choices_for_criterion.index(current) if current else 0, key=f"{session_id}_{key}", horizontal=True)
    if selected == "Select an option":
        selections.pop(key, None)
    else:
        selections[key] = selected

left, middle, right, review = st.columns(4)
if left.button("Previous Question", disabled=index == 0):
    st.session_state.question_index -= 1
    st.rerun()
if middle.button("Save Progress"):
    try:
        with Session() as db:
            save_progress(db, session_id, interviewer_id, selections)
        st.success("Draft saved.")
    except Exception as exc:
        st.error(str(exc))
if right.button("Next Question", disabled=index == len(questions) - 1):
    st.session_state.question_index += 1
    st.rerun()
if review.button("Review evaluation"):
    st.session_state.review = True
    st.rerun()
