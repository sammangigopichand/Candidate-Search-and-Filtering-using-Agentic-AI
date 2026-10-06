# Interview evaluation work log

## Architecture inspected

The repository has a standalone Ollama Interview Agent and a command line runner. Its dependencies list Streamlit and SQLAlchemy, but there are no existing web, database, or evaluation modules to extend. PostgreSQL credentials and server configuration are absent.

## Changes

- Updated Interview Agent validation to accept `advanced` and common difficulty aliases. It now rejects malformed or duplicate generated questions with specific errors so the existing three-attempt retry can run; valid extra questions are trimmed to the required distribution. The prompt now explains when to use advanced difficulty.
- Added `app/agents/evaluation_agent.py` for deterministic question, category, and overall scores. Assessable criteria have equal weight; fully unassessed groups read `Not Assessed`. The report lists positive, partial, negative, and unassessed selections, and never makes a hiring recommendation.
- Added `app/interview_store.py` with related SQLAlchemy tables for sessions, questions, criteria, responses, and reports. Drafts and final submissions are scoped to a session and interviewer. Duplicate final submission is rejected. Tables are created on first connection.
- Added `app/interviewer_ui.py` with session selection, question generation, candidate professional context, checklist navigation, draft saving, review, submission, and report display. It has no candidate answer field.
- Added focused mock based tests in `test_interview_workflow.py`, and declared the missing `ollama` and PostgreSQL driver dependencies in `requirements.txt`.

## Verification and setup

- `.venv/Scripts/python.exe -m pytest -q test_interview_workflow.py`: 8 passed. This covers generation validation and retry, checklist scoring, draft persistence, interviewer isolation, submission, and duplicate rejection. `compileall` also passed for changed Python modules.
- Install dependencies with `.venv/Scripts/python.exe -m pip install -r requirements.txt`. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL such as `postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME`. The database must already exist, and the user must be allowed to create tables. `Base.metadata.create_all` creates the five tables on first app run; there is no prior schema to migrate.
- Run the existing CLI with `.venv/Scripts/python.exe test_interview_agent.py`. Run the interface with `.venv/Scripts/python.exe -m streamlit run app/interviewer_ui.py`. Run focused tests with `.venv/Scripts/python.exe -m pytest -q test_interview_workflow.py`.
- A running Ollama service with `llama3.2:3b` is needed for new question generation. PostgreSQL and the Streamlit browser flow were not exercised here. The repository has no authentication system, so interviewer IDs entered in the interface are identifiers rather than verified identities; production use requires authentication before exposing candidate records.
