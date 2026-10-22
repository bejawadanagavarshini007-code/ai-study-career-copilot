"""
AI Study & Career Copilot — Learning, Assessment & Personalization Routes
Manages REST API endpoints for the complete learning cycle.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uuid

from ai.service import AIService
from database.db import (
    save_test_session,
    get_test_session,
    save_assignment_session,
    get_assignment_session,
    save_assignment_submission,
    get_assignment_submission,
    record_attempt_and_mastery,
    get_progress_data
)

router = APIRouter(prefix="/api", tags=["Learning Cycle"])

# --- REQUEST MODELS ---

class TopicLevelRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Target study topic")
    level: str = Field("Beginner", description="Difficulty level: Beginner, Intermediate, Advanced")

class AssignmentSubmitRequest(BaseModel):
    session_id: str = Field(..., description="Unique assignment session identifier")
    topic: str = Field(..., description="Topic of the assignment")
    level: str = Field("Beginner", description="Difficulty level")
    answers: Dict[str, str] = Field(..., description="Map of question_id to selected option")

class TestSubmitRequest(BaseModel):
    session_id: str = Field(..., description="Unique test session identifier")
    topic: str = Field(..., description="Topic of the test")
    level: str = Field("Beginner", description="Difficulty level")
    answers: Dict[str, str] = Field(default_factory=dict, description="Map of question_id to selected option")

class TargetedPracticeRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Topic name")
    weak_concept: str = Field(..., min_length=1, description="Specific concept needing remediation")
    level: str = Field("Beginner", description="Difficulty level")


# --- ROUTE HANDLERS ---

@router.post("/learn", status_code=status.HTTP_200_OK)
async def learn_topic(payload: TopicLevelRequest):
    """
    Step 1: Learn
    Generates structured topic explanation, key points, and illustrative code examples.
    """
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic name cannot be empty.")

    try:
        content = await AIService.generate_explanation(topic, payload.level)
        return content
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate learning material: {str(e)}"
        )


@router.post("/practice", status_code=status.HTTP_200_OK)
async def practice_topic(payload: TopicLevelRequest):
    """
    Step 2: Practice
    Generates interactive practice questions with immediate explanations and feedback.
    """
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic name cannot be empty.")

    try:
        data = await AIService.generate_practice_questions(topic, payload.level)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate practice questions: {str(e)}"
        )


@router.post("/assignment/generate", status_code=status.HTTP_200_OK)
async def generate_assignment(payload: TopicLevelRequest):
    """
    Step 3: Assignment Generation
    Generates applied engineering assignment questions and creates a secure session.
    """
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic name cannot be empty.")

    try:
        raw_assignment = await AIService.generate_assignment(topic, payload.level)
        full_questions = raw_assignment.get("questions", [])
        title = raw_assignment.get("title", f"{topic} Practical Assignment")
        instructions = raw_assignment.get("instructions", "Analyze the scenarios and choose the optimal solution.")

        if not full_questions:
            raise HTTPException(status_code=500, detail="No questions were generated for this assignment.")

        session_id = str(uuid.uuid4())

        # Store complete assignment (including secret correct answers) on backend
        save_assignment_session(session_id, topic, payload.level, title, instructions, full_questions)

        # Sanitize questions for the frontend (do not leak correct_answer or full explanation)
        sanitized_questions = []
        for q in full_questions:
            sanitized_questions.append({
                "question_id": q["question_id"],
                "concept": q.get("concept", "Practical Application"),
                "question": q["question"],
                "options": q["options"],
                "hint": q.get("hint")
            })

        return {
            "session_id": session_id,
            "topic": topic,
            "level": payload.level,
            "title": title,
            "instructions": instructions,
            "questions": sanitized_questions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate assignment session: {str(e)}"
        )


@router.post("/assignment/submit", status_code=status.HTTP_200_OK)
async def submit_assignment(payload: AssignmentSubmitRequest):
    """
    Evaluates submitted assignment answers, computes score, provides constructive feedback,
    prevents duplicate submissions, and preserves state.
    """
    # 1. Prevent duplicate submission by returning existing evaluation if already submitted
    existing = get_assignment_submission(payload.session_id)
    if existing:
        return {
            "session_id": existing["session_id"],
            "topic": existing["topic"],
            "difficulty": existing["difficulty"],
            "total_questions": existing["total_questions"],
            "correct_count": existing["correct_count"],
            "score_percentage": existing["score_percentage"],
            "feedback": existing["feedback"],
            "question_review": existing["review"],
            "already_submitted": True
        }

    # 2. Retrieve stored session
    session = get_assignment_session(payload.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Assignment session not found. Please refresh or regenerate the assignment."
        )

    stored_questions = session["questions"]
    total_questions = len(stored_questions)

    # 3. Validate required answers
    missing_questions = []
    for q in stored_questions:
        q_id = str(q["question_id"])
        if q_id not in payload.answers or not str(payload.answers[q_id]).strip():
            missing_questions.append(q_id)

    if missing_questions:
        raise HTTPException(
            status_code=400,
            detail=f"All {total_questions} assignment questions must be answered before submission."
        )

    # 4. Evaluate answers
    correct_count = 0
    question_review: List[Dict[str, Any]] = []

    for q in stored_questions:
        q_id = str(q["question_id"])
        correct_ans = str(q["correct_answer"]).strip()
        user_ans = str(payload.answers.get(q_id, "")).strip()
        is_correct = (user_ans.lower() == correct_ans.lower())

        if is_correct:
            correct_count += 1

        question_review.append({
            "question_id": q["question_id"],
            "concept": q.get("concept", "General"),
            "question": q["question"],
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
            "hint": q.get("hint")
        })

    score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0.0

    if score_percentage == 100:
        feedback = "Outstanding work! You demonstrated complete practical mastery of these engineering scenarios. You are fully prepared to take the final scored Assessment."
    elif score_percentage >= 65:
        feedback = "Solid effort! You correctly handled the core scenarios. Review the specific feedback notes above before proceeding to the final Assessment."
    else:
        feedback = "Keep practicing! Several important edge cases need attention. Take a moment to study the explanations above before testing your skills in the Assessment."

    # 5. Persist submission
    save_assignment_submission(
        session_id=payload.session_id,
        topic=payload.topic,
        difficulty=payload.level,
        total_questions=total_questions,
        correct_count=correct_count,
        score_percentage=round(score_percentage, 1),
        answers=payload.answers,
        review=question_review,
        feedback=feedback
    )

    return {
        "session_id": payload.session_id,
        "topic": payload.topic,
        "difficulty": payload.level,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "score_percentage": round(score_percentage, 1),
        "feedback": feedback,
        "question_review": question_review,
        "already_submitted": False
    }


@router.get("/assignment/status/{session_id}", status_code=status.HTTP_200_OK)
async def get_assignment_status(session_id: str):
    """
    Checks if an assignment was already evaluated for this session.
    """
    existing = get_assignment_submission(session_id)
    if existing:
        return {"submitted": True, "data": existing}
    return {"submitted": False}


@router.post("/test/generate", status_code=status.HTTP_200_OK)
async def generate_test(payload: TopicLevelRequest):
    """
    Step 3: Test Generation (Secure Assessment)
    Creates randomized assessment questions and establishes a secure session.
    
    SECURITY GUARANTEE:
    The correct answers and detailed explanations are stored strictly on the server database.
    The response sent to the client contains ONLY question IDs, concepts, question text, and options.
    """
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic name cannot be empty.")

    try:
        raw_test = await AIService.generate_test_questions(topic, payload.level)
        full_questions = raw_test.get("questions", [])

        if not full_questions:
            raise HTTPException(status_code=500, detail="No questions were generated for this assessment.")

        session_id = str(uuid.uuid4())

        # Store complete questions (including correct_answer) in the backend SQLite DB
        save_test_session(session_id, topic, payload.level, full_questions)

        # Sanitize questions for the frontend (NEVER expose correct_answer or explanation)
        sanitized_questions = []
        for q in full_questions:
            sanitized_questions.append({
                "question_id": q["question_id"],
                "concept": q.get("concept", "General"),
                "question": q["question"],
                "options": q["options"]
            })

        return {
            "session_id": session_id,
            "topic": topic,
            "level": payload.level,
            "questions": sanitized_questions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate test session: {str(e)}"
        )


@router.post("/test/submit", status_code=status.HTTP_200_OK)
async def submit_test(payload: TestSubmitRequest):
    """
    Step 4: Analyze & Assessment Evaluation
    Evaluates submitted answers against the backend-stored session answer key,
    computes scores, maps mistakes to specific concepts, and updates persistence.
    """
    session = get_test_session(payload.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Test session not found or has expired. Please initiate a new test."
        )

    stored_questions = session["questions"]
    total_questions = len(stored_questions)
    correct_count = 0

    concept_stats: Dict[str, Dict[str, int]] = {}
    question_review: List[Dict[str, Any]] = []

    for q in stored_questions:
        q_id = str(q["question_id"])
        concept = q.get("concept", "General Concept")
        correct_ans = str(q["correct_answer"]).strip()
        user_ans = str(payload.answers.get(q_id, "")).strip()

        is_correct = (user_ans.lower() == correct_ans.lower())
        if is_correct:
            correct_count += 1

        # Track concept statistics
        if concept not in concept_stats:
            concept_stats[concept] = {"total": 0, "correct": 0}
        concept_stats[concept]["total"] += 1
        if is_correct:
            concept_stats[concept]["correct"] += 1

        # Build detailed review
        question_review.append({
            "question_id": q["question_id"],
            "concept": concept,
            "question": q["question"],
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "is_correct": is_correct,
            "explanation": q.get("explanation", "")
        })

    score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0.0

    # Classify concepts into strong vs weak
    concept_analysis = []
    weak_concepts = []

    for concept, stats_dict in concept_stats.items():
        tot = stats_dict["total"]
        cor = stats_dict["correct"]
        acc = (cor / tot * 100) if tot > 0 else 0.0
        status_label = "Needs Practice" if acc < 75.0 else "Strong"
        if acc < 75.0:
            weak_concepts.append(concept)

        concept_analysis.append({
            "concept": concept,
            "total": tot,
            "correct": cor,
            "accuracy": round(acc, 1),
            "status": status_label
        })

    # Record to SQLite database
    attempt_id = record_attempt_and_mastery(
        session_id=payload.session_id,
        topic=payload.topic,
        difficulty=payload.level,
        total_questions=total_questions,
        correct_count=correct_count,
        score_percentage=round(score_percentage, 1),
        answers_review=question_review
    )

    summary_text = (
        f"You scored {correct_count} out of {total_questions} ({round(score_percentage)}%). "
        + ("All concepts mastered!" if not weak_concepts else f"Identified {len(weak_concepts)} concept(s) requiring reinforcement.")
    )

    return {
        "attempt_id": attempt_id,
        "topic": payload.topic,
        "difficulty": payload.level,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "score_percentage": round(score_percentage, 1),
        "summary": summary_text,
        "concept_analysis": concept_analysis,
        "weak_concepts": weak_concepts,
        "question_review": question_review
    }


@router.post("/targeted-practice", status_code=status.HTTP_200_OK)
async def targeted_practice(payload: TargetedPracticeRequest):
    """
    Step 5: Personalization / Targeted Practice
    Produces focused remedial explanation, practical code pattern, and a mini-drill
    specifically targeting the detected weak concept.
    """
    topic = payload.topic.strip()
    weak_concept = payload.weak_concept.strip()

    if not topic or not weak_concept:
        raise HTTPException(status_code=400, detail="Topic and weak concept are both required.")

    try:
        drill = await AIService.generate_targeted_practice(topic, weak_concept, payload.level)
        return drill
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate targeted practice: {str(e)}"
        )


@router.get("/progress", status_code=status.HTTP_200_OK)
async def get_progress():
    """
    Step 6: Progress & Analytics
    Retrieves cumulative metrics, topics studied, score history, and concept mastery matrix.
    """
    try:
        data = get_progress_data()
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve learning progress: {str(e)}"
        )
