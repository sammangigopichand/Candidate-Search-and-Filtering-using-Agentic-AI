import json
from typing import Any

import ollama


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "llama3.2:3b"

MAX_RETRIES = 2

REQUIRED_CATEGORIES = {
    "technical": 3,
    "project": 2,
    "behavioral": 1,
}

VALID_DIFFICULTIES = {
    "foundational",
    "intermediate",
    "advanced",
}

DIFFICULTY_ALIASES = {"basic": "foundational", "beginner": "foundational", "entry level": "foundational", "medium": "intermediate", "mid level": "intermediate", "expert": "advanced", "senior": "advanced"}

EVALUATION_OPTIONS = [
    "Yes",
    "Partially",
    "No",
    "Not Assessed",
]


# ============================================================
# CATEGORY NORMALIZATION
# ============================================================

CATEGORY_ALIASES = {

    # Technical questions
    "technical": "technical",
    "technical question": "technical",
    "technical-based": "technical",
    "technical based": "technical",

    # Project questions
    "project": "project",
    "project-based": "project",
    "project based": "project",
    "project-based question": "project",
    "project question": "project",
    "project related": "project",
    "project-related": "project",

    # Behavioral questions
    "behavioral": "behavioral",
    "behavioural": "behavioral",
    "behavioral question": "behavioral",
    "behavioural question": "behavioral",
    "behavioral-based": "behavioral",
    "behavioural-based": "behavioral",
    "situational": "behavioral",
}


def normalize_category(category: str) -> str:

    """
    Convert alternative category names into
    standardized internal category names.
    """

    category = str(
        category or ""
    ).strip().lower()

    category = " ".join(
        category.split()
    )

    return CATEGORY_ALIASES.get(
        category,
        category,
    )


# ============================================================
# 1. BUILD INTERVIEW CONTEXT
# ============================================================

def build_interview_context(
    candidate_profile: dict,
    job_profile: dict,
    experience_report: dict,
) -> dict:

    """
    Extract information required for generating
    interview questions and evaluation checklists.

    Personal contact information is excluded.
    """

    return {

        "target_job": job_profile.get(
            "job_title"
        ),

        "role_summary": job_profile.get(
            "role_summary"
        ),

        "required_skills": (job_profile.get("required_skills") or [])[:30],

        "preferred_skills": (job_profile.get("preferred_skills") or [])[:20],

        "responsibilities": (job_profile.get("responsibilities") or [])[:10],

        "candidate_skills": (candidate_profile.get("skills") or [])[:30],

        "candidate_projects": [
            {
                "name": project.get("name"),
                "description": str(project.get("description") or "")[:600],
                "technologies": (project.get("technologies") or [])[:10],
            }
            for project in (candidate_profile.get("projects") or [])[:4]
            if isinstance(project, dict)
        ],

        "candidate_experience": [
            {
                "job_title": item.get("job_title"),
                "company": item.get("company"),
                "responsibilities": (item.get("responsibilities") or [])[:3],
                "technologies": (item.get("technologies") or [])[:10],
            }
            for item in (candidate_profile.get("experience") or [])[:4]
            if isinstance(item, dict)
        ],

        "experience_level": experience_report.get(
            "provisional_experience_level",
            "Undetermined",
        ),

        "possible_experience_levels": (
            experience_report.get(
                "possible_experience_levels"
            ) or []
        ),
    }


# ============================================================
# 2. VALIDATE A SINGLE QUESTION
# ============================================================

def validate_single_question(
    item: Any,
) -> dict:

    """
    Validate one generated interview question.

    Normalize category names before validation.

    Return a cleaned question dictionary.
    """

    if not isinstance(item, dict):

        raise ValueError(
            "Question must be a JSON object."
        )

    # --------------------------------------------------------
    # CATEGORY NORMALIZATION AND VALIDATION
    # --------------------------------------------------------

    category = normalize_category(
        item.get("category")
    )

    if category not in REQUIRED_CATEGORIES:

        raise ValueError(
            f"Invalid question category: {category}"
        )

    # --------------------------------------------------------
    # DIFFICULTY VALIDATION
    # --------------------------------------------------------

    difficulty = str(
        item.get("difficulty") or ""
    ).strip().lower()

    difficulty = DIFFICULTY_ALIASES.get(difficulty.replace("-", " "), difficulty)

    if difficulty not in VALID_DIFFICULTIES:

        raise ValueError(
            f"Invalid question difficulty: {difficulty}"
        )

    # --------------------------------------------------------
    # QUESTION VALIDATION
    # --------------------------------------------------------

    question = item.get("question")

    if (
        not isinstance(question, str)
        or not question.strip()
    ):

        raise ValueError(
            "Question text cannot be empty."
        )

    # --------------------------------------------------------
    # EXPECTED CONCEPTS VALIDATION
    # --------------------------------------------------------

    expected_concepts = item.get(
        "expected_concepts"
    )

    if (
        not isinstance(expected_concepts, list)
        or not 2 <= len(expected_concepts) <= 5
    ):

        raise ValueError(
            "Expected concepts must contain "
            "between 2 and 5 items."
        )

    cleaned_concepts = []

    for concept in expected_concepts:

        if (
            not isinstance(concept, str)
            or not concept.strip()
        ):

            raise ValueError(
                "Expected concepts must contain "
                "non-empty strings."
            )

        cleaned_concepts.append(
            concept.strip()
        )

    # --------------------------------------------------------
    # EVALUATION CRITERIA VALIDATION
    # --------------------------------------------------------

    evaluation_criteria = item.get(
        "evaluation_criteria"
    )

    if (
        not isinstance(evaluation_criteria, list)
        or not 3 <= len(evaluation_criteria) <= 5
    ):

        raise ValueError(
            "Evaluation criteria must contain "
            "between 3 and 5 items."
        )

    cleaned_criteria = []

    for criterion in evaluation_criteria:

        if (
            not isinstance(criterion, str)
            or not criterion.strip()
        ):

            raise ValueError(
                "Evaluation criteria must contain "
                "non-empty strings."
            )

        cleaned_criteria.append(
            criterion.strip()
        )

    # --------------------------------------------------------
    # RETURN VALIDATED QUESTION
    # --------------------------------------------------------

    return {

        "category": category,

        "difficulty": difficulty,

        "question": question.strip(),

        "expected_concepts": cleaned_concepts,

        "evaluation_criteria": cleaned_criteria,
    }


# ============================================================
# 3. VALIDATE AND SELECT REQUIRED QUESTIONS
# ============================================================

def validate_questions(
    data: Any,
) -> list[dict]:

    """
    Validate all generated questions.

    Select exactly:

        3 technical questions
        2 project questions
        1 behavioral question

    Extra questions are ignored after validation.

    Invalid questions cause a validation error and trigger generation retry.

    Raise ValueError if the required distribution
    cannot be satisfied.
    """

    if not isinstance(data, dict):

        raise ValueError(
            "The model response must be a JSON object."
        )

    questions = data.get("questions")

    if not isinstance(questions, list):

        raise ValueError(
            "The response must contain a questions list."
        )

    if not questions:

        raise ValueError(
            "The generated questions list is empty."
        )

    # --------------------------------------------------------
    # VALIDATE ALL GENERATED QUESTIONS
    # --------------------------------------------------------

    valid_questions = []
    for index, item in enumerate(questions, start=1):
        try:
            valid_questions.append(validate_single_question(item))
        except ValueError as exc:
            raise ValueError(f"Question {index}: {exc}") from exc

    # --------------------------------------------------------
    # SELECT REQUIRED QUESTION DISTRIBUTION
    # --------------------------------------------------------

    selected_questions = []

    category_counts = {
        category: 0
        for category in REQUIRED_CATEGORIES
    }

    seen_questions = set()

    for item in valid_questions:

        category = item["category"]

        normalized_question = " ".join(
            item["question"].lower().split()
        )

        # Skip duplicate questions

        if normalized_question in seen_questions:
            raise ValueError(f"Duplicate question: {item['question']}")
        seen_questions.add(normalized_question)

        # Skip questions when the category quota is reached

        if (
            category_counts[category]
            >= REQUIRED_CATEGORIES[category]
        ):

            continue

        selected_questions.append(
            item
        )

        category_counts[category] += 1


    # --------------------------------------------------------
    # VALIDATE FINAL QUESTION DISTRIBUTION
    # --------------------------------------------------------

    if category_counts != REQUIRED_CATEGORIES:

        raise ValueError(
            "Ollama did not generate the required "
            "question distribution. "
            f"Expected {REQUIRED_CATEGORIES}, "
            f"received {category_counts}."
        )

    # --------------------------------------------------------
    # ASSIGN QUESTION AND CRITERION IDS
    # --------------------------------------------------------

    validated_questions = []

    for question_index, item in enumerate(
        selected_questions,
        start=1,
    ):

        validated_criteria = []

        for criterion_index, criterion in enumerate(
            item["evaluation_criteria"],
            start=1,
        ):

            validated_criteria.append(
                {
                    "criterion_id": (
                        f"Q{question_index}_C{criterion_index}"
                    ),

                    "criterion": criterion,

                    "options": EVALUATION_OPTIONS.copy(),

                    "selected_option": None,
                }
            )

        validated_questions.append(
            {
                "question_id": question_index,

                "category": item["category"],

                "difficulty": item["difficulty"],

                "question": item["question"],

                "expected_concepts": (
                    item["expected_concepts"]
                ),

                "evaluation_criteria": (
                    validated_criteria
                ),
            }
        )

    return validated_questions


# ============================================================
# 4. BUILD INTERVIEW GENERATION PROMPT
# ============================================================

def build_interview_prompt(
    context: dict,
) -> str:

    """
    Create the prompt used by Ollama to generate
    interview questions and evaluation checklists.
    """

    prompt = f"""
You are an interview-question generation assistant.

Your task is to generate interview questions and evaluation
checklists for a human interviewer.

Generate EXACTLY SIX interview questions.

IMPORTANT QUESTION DISTRIBUTION:

1. EXACTLY THREE technical questions.
2. EXACTLY TWO project-based questions.
3. EXACTLY ONE behavioral question.

Total questions = 6.

Do not generate additional questions.

Do not generate fewer than six questions.

Use only the supplied candidate and job information.

Do not invent employment responsibilities,
professional experience, certifications,
or completed projects.

EXPERIENCE LEVEL:

The candidate's experience level may be "Undetermined".

If the experience level is undetermined, generate
a mixture of foundational and intermediate questions.

Do not assume a specific seniority level.

Use only foundational, intermediate, or advanced difficulty.
Use advanced only if the job and documented experience justify it.

-------------------------------------------------------
TECHNICAL QUESTIONS
-------------------------------------------------------

Generate exactly 3 technical questions.

Questions must be based on the job's required skills.

Each technical question should assess relevant
technical knowledge or problem-solving ability.

-------------------------------------------------------
PROJECT QUESTIONS
-------------------------------------------------------

Generate exactly 2 project-based questions.

Use the candidate's documented projects.

Ask about project implementation, technical decisions,
challenges, architecture, or problem-solving.

Do not claim the candidate used a technology unless
it appears in the project information.

If no projects are documented, ask questions about
how the candidate would approach relevant job tasks.

Do not invent candidate projects.

-------------------------------------------------------
BEHAVIORAL QUESTION
-------------------------------------------------------

Generate exactly 1 behavioral question.

The question must assess a job-related situation.

Do not ask about personal characteristics unrelated
to job performance.

-------------------------------------------------------
EXPECTED CONCEPTS
-------------------------------------------------------

For each question, generate exactly 2 expected concepts.

Expected concepts should help a human interviewer
understand what to look for in the candidate's response.

They are guidance, not a definitive answer key.

-------------------------------------------------------
EVALUATION CHECKLIST
-------------------------------------------------------

For each question, generate exactly 3 evaluation criteria.

Each criterion must describe one observable,
job-related aspect of the candidate's response.

The interviewer will evaluate each criterion using:

Yes
Partially
No
Not Assessed

Examples of good criteria:

"Correctly explains supervised learning"

"Identifies the difference between labeled
and unlabeled data"

"Explains the technical architecture of the
documented project"

"Describes a relevant problem-solving approach"

Avoid vague criteria such as:

"Candidate is intelligent"

"Candidate has a good personality"

"Candidate looks confident"

The evaluation criteria must be specific,
clear, and relevant to the question.

Do not generate candidate answers.

Do not include candidate suitability scores.

Do not include hiring recommendations.

-------------------------------------------------------
OUTPUT FORMAT
-------------------------------------------------------

Return ONLY a valid JSON object.

Do not include Markdown.

Do not include explanations outside the JSON.

Use this exact structure:

{{
    "questions": [
        {{
            "category": "technical",
            "difficulty": "foundational",
            "question": "Explain supervised learning.",
            "expected_concepts": [
                "Labeled data",
                "Classification",
                "Regression"
            ],
            "evaluation_criteria": [
                "Correctly explains supervised learning",
                "Explains the role of labeled data",
                "Provides an appropriate practical example"
            ]
        }}
    ]
}}

The JSON example above demonstrates the structure only.

Your actual response MUST contain exactly SIX questions
with the required category distribution.

IMPORTANT:

Use ONLY these category names:

technical
project
behavioral

Do not use "project-based" as a category name.

-------------------------------------------------------
CANDIDATE AND JOB CONTEXT
-------------------------------------------------------

{json.dumps(context, indent=2, ensure_ascii=False)}
"""

    return prompt


# ============================================================
# 5. GENERATE INTERVIEW QUESTIONS
# ============================================================

def generate_interview_questions(
    candidate_profile: dict,
    job_profile: dict,
    experience_report: dict,
) -> dict:

    """
    Generate six interview questions and their
    evaluation checklists using Ollama.

    Retry generation when the model returns
    invalid JSON or an incorrect question distribution.
    """

    # --------------------------------------------------------
    # BUILD CONTEXT
    # --------------------------------------------------------

    context = build_interview_context(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        experience_report=experience_report,
    )

    # --------------------------------------------------------
    # BUILD PROMPT
    # --------------------------------------------------------

    prompt = build_interview_prompt(
        context
    )

    questions = None

    last_error = None

    # --------------------------------------------------------
    # GENERATION WITH RETRIES
    # --------------------------------------------------------

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        print(
            f"\nGenerating interview questions "
            f"and evaluation checklists "
            f"(Attempt {attempt}/{MAX_RETRIES})..."
        )

        try:

            response = ollama.chat(
                model=MODEL_NAME,

                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],

                format="json",

                keep_alive="10m",

                options={
                    "temperature": 0.1,
                    "num_predict": 3000,
                },
            )

            # ------------------------------------------------
            # EXTRACT RESPONSE
            # ------------------------------------------------

            response_text = response[
                "message"
            ]["content"]

            # ------------------------------------------------
            # PARSE JSON
            # ------------------------------------------------

            generated_data = json.loads(
                response_text
            )

            # ------------------------------------------------
            # VALIDATE QUESTIONS
            # ------------------------------------------------

            questions = validate_questions(
                generated_data
            )

            print(
                "\nInterview questions and "
                "evaluation checklists generated "
                "successfully!"
            )

            break

        except (
            ValueError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
        ) as exc:

            last_error = exc

            print(
                f"\nGeneration attempt {attempt} "
                f"failed: {exc}"
            )

            if attempt < MAX_RETRIES:

                print(
                    "Retrying interview question "
                    "generation..."
                )

    # --------------------------------------------------------
    # CHECK GENERATION RESULT
    # --------------------------------------------------------

    if questions is None:

        raise RuntimeError(
            "Interview question generation failed "
            f"after {MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    # --------------------------------------------------------
    # RETURN FINAL INTERVIEW REPORT
    # --------------------------------------------------------

    return {

        "target_job": job_profile.get(
            "job_title"
        ),

        "experience_level": experience_report.get(
            "provisional_experience_level",
            "Undetermined",
        ),

        "questions": questions,

        "note": (
            "Questions, expected concepts, and evaluation "
            "criteria were generated by an LLM. "
            "Review them for technical accuracy and job "
            "relevance before using them in an interview."
        ),
    }
