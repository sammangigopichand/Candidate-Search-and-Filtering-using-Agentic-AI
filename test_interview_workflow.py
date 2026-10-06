import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.evaluation_agent import evaluate_interview
from app.agents.interview_agent import generate_interview_questions, validate_questions
from app.interview_store import Base, create_interview, get_interview, interview_data, saved_selections, save_progress, submit_evaluation


def generated(extra=False):
    categories = ["technical"] * 3 + ["project-based"] * 2 + ["behavioural"]
    if extra:
        categories.append("technical")
    return {"questions": [{"category": category, "difficulty": "advanced" if index == 0 else "intermediate", "question": f"Explain task {index}?", "expected_concepts": ["Concept A", "Concept B"], "evaluation_criteria": ["Describes approach", "Explains tradeoffs", "Gives example"]} for index, category in enumerate(categories)]}


def test_question_validation_and_extra():
    questions = validate_questions(generated(extra=True))
    assert len(questions) == 6
    assert [q["category"] for q in questions].count("project") == 2
    assert questions[0]["difficulty"] == "advanced"


@pytest.mark.parametrize("change", [
    lambda data: data["questions"][0].update(evaluation_criteria=["Only one"]),
    lambda data: data["questions"][0].update(question="Explain task 1?"),
    lambda data: data["questions"][3].update(category="technical"),
])
def test_invalid_generation(change):
    data = generated()
    change(data)
    with pytest.raises(ValueError):
        validate_questions(data)


def test_retry_invalid_json():
    answers = iter(["broken", json.dumps(generated())])
    with patch("app.agents.interview_agent.ollama.chat", side_effect=lambda **kwargs: {"message": {"content": next(answers)}}) as call:
        result = generate_interview_questions({}, {}, {})
    assert len(result["questions"]) == 6
    assert call.call_count == 2


def test_retry_exhausted():
    with patch("app.agents.interview_agent.ollama.chat", return_value={"message": {"content": "{"}}) as call:
        with pytest.raises(RuntimeError, match="after 3 attempts"):
            generate_interview_questions({}, {}, {})
    assert call.call_count == 3


def test_scoring_options():
    questions = validate_questions(generated())
    session = {"candidate_id": "c", "job_id": "j", "interviewer_id": "i", "target_job": "Engineer", "interview_round": "1", "interview_date": datetime.now(timezone.utc).isoformat(), "questions": questions}
    ids = [c["criterion_id"] for q in questions for c in q["evaluation_criteria"]]
    selections = {key: "Yes" for key in ids}
    assert evaluate_interview(session, selections)["overall_score"] == 100
    selections[ids[0]] = "Partially"
    selections[ids[1]] = "No"
    selections[ids[2]] = "Not Assessed"
    report = evaluate_interview(session, selections)
    assert report["question_results"][0]["score"] == 25
    assert len(report["unassessed_criteria"]) == 1
    assert evaluate_interview(session, {key: "Not Assessed" for key in ids})["overall_score"] == "Not Assessed"
    with pytest.raises(ValueError, match="Select a valid option"):
        evaluate_interview(session, {})


def test_draft_submission_and_isolation():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    questions = validate_questions(generated())
    with Session() as db:
        sid = create_interview(db, candidate_id="candidate", job_id="job", interviewer_id="alice", target_job="Engineer", interview_round="1", candidate_summary={"skills": ["Python"]}, questions=questions)
        criteria = [c["criterion_id"] for q in questions for c in q["evaluation_criteria"]]
        save_progress(db, sid, "alice", {criteria[0]: "Yes"})
        assert saved_selections(get_interview(db, sid, "alice")) == {criteria[0]: "Yes"}
        with pytest.raises(ValueError):
            get_interview(db, sid, "bob")
        report = submit_evaluation(db, sid, "alice", {key: "No" for key in criteria[1:]})
        assert report["overall_score"] > 0
        assert get_interview(db, sid, "alice").status == "submitted"
        with pytest.raises(ValueError, match="already been submitted"):
            submit_evaluation(db, sid, "alice", {key: "No" for key in criteria})
