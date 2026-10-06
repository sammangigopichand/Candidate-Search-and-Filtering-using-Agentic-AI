"""PostgreSQL persistence for checklist interviews.

Set DATABASE_URL to a SQLAlchemy PostgreSQL URL before using this module.
"""

import os
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.agents.evaluation_agent import OPTIONS, evaluate_interview



import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")







class Base(DeclarativeBase):
    pass


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(String(255), nullable=False)
    job_id: Mapped[str] = mapped_column(String(255), nullable=False)
    interviewer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    target_job: Mapped[str] = mapped_column(String(255), nullable=False)
    interview_round: Mapped[str] = mapped_column(String(100), nullable=False)
    interview_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    candidate_summary: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    questions: Mapped[list["InterviewQuestion"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="InterviewQuestion.position")
    responses: Mapped[list["InterviewerResponse"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    report: Mapped["EvaluationReport | None"] = relationship(back_populates="session", uselist=False, cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("interview_sessions.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(30), nullable=False)
    question: Mapped[str] = mapped_column(String, nullable=False)
    expected_concepts: Mapped[list] = mapped_column(JSON, nullable=False)
    session: Mapped[InterviewSession] = relationship(back_populates="questions")
    criteria: Mapped[list["EvaluationCriterion"]] = relationship(back_populates="question_record", cascade="all, delete-orphan", order_by="EvaluationCriterion.position")
    __table_args__ = (UniqueConstraint("session_id", "question_id"),)


class EvaluationCriterion(Base):
    __tablename__ = "evaluation_criteria"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_record_id: Mapped[str] = mapped_column(ForeignKey("interview_questions.id"), nullable=False)
    criterion_id: Mapped[str] = mapped_column(String(30), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    criterion: Mapped[str] = mapped_column(String, nullable=False)
    question_record: Mapped[InterviewQuestion] = relationship(back_populates="criteria")


class InterviewerResponse(Base):
    __tablename__ = "interviewer_responses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("interview_sessions.id"), nullable=False)
    criterion_record_id: Mapped[str] = mapped_column(ForeignKey("evaluation_criteria.id"), nullable=False)
    interviewer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    selected_option: Mapped[str] = mapped_column(String(20), nullable=False)
    session: Mapped[InterviewSession] = relationship(back_populates="responses")
    __table_args__ = (UniqueConstraint("session_id", "criterion_record_id", "interviewer_id"),)


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("interview_sessions.id"), unique=True, nullable=False)
    calculated_score: Mapped[float | None] = mapped_column(nullable=True)
    evaluation_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    session: Mapped[InterviewSession] = relationship(back_populates="report")


def database_session():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Set DATABASE_URL to a PostgreSQL SQLAlchemy URL.")
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_interview(db, *, candidate_id, job_id, interviewer_id, target_job, interview_round, candidate_summary, questions):
    record = InterviewSession(id=str(uuid4()), candidate_id=candidate_id, job_id=job_id, interviewer_id=interviewer_id, target_job=target_job, interview_round=interview_round, interview_date=datetime.now(timezone.utc), candidate_summary=candidate_summary, status="draft")
    for position, item in enumerate(questions):
        question = InterviewQuestion(id=str(uuid4()), question_id=item["question_id"], position=position, category=item["category"], difficulty=item["difficulty"], question=item["question"], expected_concepts=item["expected_concepts"])
        for index, criterion in enumerate(item["evaluation_criteria"]):
            question.criteria.append(EvaluationCriterion(id=str(uuid4()), criterion_id=criterion["criterion_id"], position=index, criterion=criterion["criterion"]))
        record.questions.append(question)
    db.add(record)
    db.commit()
    return record.id


def get_interview(db, session_id, interviewer_id):
    record = db.get(InterviewSession, session_id)
    if record is None or record.interviewer_id != interviewer_id:
        raise ValueError("Interview session not found for this interviewer.")
    return record


def interview_data(record):
    return {"candidate_id": record.candidate_id, "job_id": record.job_id, "interviewer_id": record.interviewer_id, "target_job": record.target_job, "interview_round": record.interview_round, "interview_date": record.interview_date.isoformat(), "questions": [{"question_id": q.question_id, "category": q.category, "difficulty": q.difficulty, "question": q.question, "expected_concepts": q.expected_concepts, "evaluation_criteria": [{"criterion_id": c.criterion_id, "criterion": c.criterion} for c in q.criteria]} for q in record.questions]}


def saved_selections(record):
    lookup = {c.id: c.criterion_id for q in record.questions for c in q.criteria}
    return {lookup[r.criterion_record_id]: r.selected_option for r in record.responses if r.interviewer_id == record.interviewer_id and r.criterion_record_id in lookup}


def save_progress(db, session_id, interviewer_id, selections):
    record = get_interview(db, session_id, interviewer_id)
    if record.status == "submitted":
        raise ValueError("This interview has already been submitted.")
    criteria = {c.criterion_id: c for q in record.questions for c in q.criteria}
    if set(selections) - set(criteria):
        raise ValueError("Selection contains an unknown criterion.")
    existing = {r.criterion_record_id: r for r in record.responses if r.interviewer_id == interviewer_id}
    for key, option in selections.items():
        if option not in OPTIONS:
            raise ValueError(f"Invalid option for {key}.")
        criterion = criteria[key]
        if criterion.id in existing:
            existing[criterion.id].selected_option = option
        else:
            db.add(InterviewerResponse(id=str(uuid4()), session_id=session_id, criterion_record_id=criterion.id, interviewer_id=interviewer_id, selected_option=option))
    db.commit()
    db.expire_all()


def submit_evaluation(db, session_id, interviewer_id, selections):
    record = get_interview(db, session_id, interviewer_id)
    if record.status == "submitted":
        raise ValueError("This interview has already been submitted.")
    combined = saved_selections(record) | selections
    report = evaluate_interview(interview_data(record), combined)
    save_progress(db, session_id, interviewer_id, selections)
    record.status = "submitted"
    record.report = EvaluationReport(id=str(uuid4()), calculated_score=report["overall_score"] if isinstance(report["overall_score"], float) else None, evaluation_timestamp=datetime.fromisoformat(report["evaluation_timestamp"]), data=report)
    db.commit()
    return report


def find_existing_interview(
    db,
    candidate_id: str,
    job_id: str,
    interview_round: str,
):
    """
    Find an existing interview for the same
    candidate, job and interview round.
    """

    statement = (
        select(InterviewSession)
        .where(
            InterviewSession.candidate_id == candidate_id,
            InterviewSession.job_id == job_id,
            InterviewSession.interview_round == interview_round,
        )
        .order_by(
            InterviewSession.interview_date.desc()
        )
    )

    return db.scalars(statement).first()









def get_interview_details(
    db,
    session_id: str,
):
    """
    Load an interview session with its generated questions
    and evaluation criteria for recruiter review.
    """

    record = db.get(
        InterviewSession,
        session_id,
    )

    if record is None:
        return None

    return {
        "id": record.id,
        "candidate_id": record.candidate_id,
        "job_id": record.job_id,
        "interviewer_id": record.interviewer_id,
        "target_job": record.target_job,
        "interview_round": record.interview_round,
        "interview_date": (
            record.interview_date.isoformat()
            if record.interview_date
            else None
        ),
        "status": record.status,
        "candidate_summary": (
            record.candidate_summary or {}
        ),
        "questions": [
            {
                "question_id": question.question_id,
                "position": question.position,
                "category": question.category,
                "difficulty": question.difficulty,
                "question": question.question,
                "expected_concepts": (
                    question.expected_concepts or []
                ),
                "evaluation_criteria": [
                    {
                        "criterion_id": criterion.criterion_id,
                        "criterion": criterion.criterion,
                    }
                    for criterion in question.criteria
                ],
            }
            for question in record.questions
        ],
    }






def clear_interview_processing_data(db):
    """
    Delete all interview-related candidate processing data.

    Deletion order follows PostgreSQL foreign-key dependencies.
    """

    # 1. Depends on evaluation_criteria and interview_sessions
    db.query(InterviewerResponse).delete(
        synchronize_session=False
    )

    # 2. Depends on interview_questions
    db.query(EvaluationCriterion).delete(
        synchronize_session=False
    )

    # 3. Depends on interview_sessions
    db.query(EvaluationReport).delete(
        synchronize_session=False
    )

    # 4. Depends on interview_sessions
    db.query(InterviewQuestion).delete(
        synchronize_session=False
    )

    # 5. Parent interview record
    db.query(InterviewSession).delete(
        synchronize_session=False
    )

    db.commit()