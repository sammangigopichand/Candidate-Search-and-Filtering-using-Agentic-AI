"""Deterministic scoring of interviewer checklist selections."""

from datetime import datetime, timezone

OPTIONS = {"Yes": 2, "Partially": 1, "No": 0, "Not Assessed": None}


def evaluate_interview(session: dict, selections: dict[str, str]) -> dict:
    """Score assessed criteria with equal weight; exclude unassessed criteria.

    A category and the overall score are earned points divided by the maximum
    assessable points in that group. An entirely unassessed group is labelled
    ``Not Assessed``. Every criterion needs an explicit selection.
    """
    totals = {category: [0, 0] for category in ("technical", "project", "behavioral")}
    results = []
    seen = set()
    for question in session["questions"]:
        earned = maximum = 0
        assessments = []
        for criterion in question["evaluation_criteria"]:
            key = criterion["criterion_id"]
            if key in seen:
                raise ValueError(f"Duplicate criterion ID: {key}")
            seen.add(key)
            option = selections.get(key)
            if option not in OPTIONS:
                raise ValueError(f"Select a valid option for {key}.")
            points = OPTIONS[option]
            if points is not None:
                earned += points
                maximum += 2
            assessments.append({"criterion_id": key, "criterion": criterion["criterion"], "selected_option": option})
        category = question["category"]
        if category not in totals:
            raise ValueError(f"Unknown category: {category}")
        totals[category][0] += earned
        totals[category][1] += maximum
        results.append({"question_id": question["question_id"], "question": question["question"], "category": category, "score": round(100 * earned / maximum, 2) if maximum else "Not Assessed", "criteria": assessments})

    def score(pair):
        return round(100 * pair[0] / pair[1], 2) if pair[1] else "Not Assessed"

    all_totals = [sum(v[i] for v in totals.values()) for i in (0, 1)]
    groups = {"Yes": [], "Partially": [], "No": [], "Not Assessed": []}
    for result in results:
        for item in result["criteria"]:
            groups[item["selected_option"]].append({"question_id": result["question_id"], "criterion_id": item["criterion_id"], "criterion": item["criterion"]})
    return {
        "candidate_id": session["candidate_id"],
        "job_id": session["job_id"],
        "target_job": session["target_job"],
        "interview_round": session["interview_round"],
        "interview_date": session["interview_date"],
        "interviewer_id": session["interviewer_id"],
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "question_results": results,
        "technical_score": score(totals["technical"]),
        "project_score": score(totals["project"]),
        "behavioral_score": score(totals["behavioral"]),
        "overall_score": score(all_totals),
        "observed_strengths": groups["Yes"],
        "partially_met": groups["Partially"],
        "areas_requiring_improvement": groups["No"],
        "unassessed_criteria": groups["Not Assessed"],
        "score_basis": "Interviewer checklist assessments; equal weight per assessed criterion. No hiring decision is made.",
    }
