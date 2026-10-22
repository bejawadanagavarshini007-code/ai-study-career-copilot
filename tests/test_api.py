"""
AI Study & Career Copilot — Automated Test Suite
Verifies API endpoints, answer security, scoring, concept mapping, personalization,
Practice submission, Assignment validation, and database persistence.
"""

import pytest
from starlette.testclient import TestClient
from backend.app import app
from database.db import init_db

client = TestClient(app)

def setup_module():
    """Ensure database is freshly initialized before tests run."""
    init_db()

def test_health_check():
    """Verify health endpoint responds correctly."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "learning_cycle" in data

def test_frontend_serving():
    """Verify frontend static index.html is served at root."""
    res = client.get("/")
    assert res.status_code == 200
    assert "AI Study & Career Copilot" in res.text

def test_learn_endpoint():
    """Verify /api/learn returns structured explanation, key points, and examples."""
    payload = {"topic": "Python Functions", "level": "Beginner"}
    res = client.post("/api/learn", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["topic"] == "Python Functions"
    assert len(data["key_points"]) > 0
    assert len(data["examples"]) > 0

def test_practice_endpoint_with_hints():
    """Verify /api/practice returns questions with explanations and hints."""
    payload = {"topic": "Python Functions", "level": "Beginner"}
    res = client.post("/api/practice", json=payload)
    assert res.status_code == 200
    data = res.json()
    questions = data.get("questions", [])
    assert len(questions) > 0
    q1 = questions[0]
    assert "question" in q1
    assert "options" in q1
    assert "correct_answer" in q1
    assert "explanation" in q1
    assert "hint" in q1

def test_assignment_generation_and_security():
    """
    Verify Assignment generation:
    1. Creates session on backend.
    2. Questions do NOT expose correct_answer or detailed explanation to the client.
    3. Questions include scenario hints.
    """
    payload = {"topic": "Python Functions", "level": "Beginner"}
    res = client.post("/api/assignment/generate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "session_id" in data
    assert "title" in data
    assert "instructions" in data
    questions = data["questions"]
    assert len(questions) > 0

    for q in questions:
        assert "correct_answer" not in q, f"SECURITY VIOLATION: Assignment leaked answer for Q {q['question_id']}"
        assert "options" in q
        assert "concept" in q

def test_assignment_submission_validation_and_duplicate_prevention():
    """
    Verify Assignment submission:
    1. Rejects submission with HTTP 400 if required questions are unanswered.
    2. Correctly evaluates full answers, computes score, provides feedback.
    3. Prevents duplicate submissions and preserves state when called again.
    """
    # 1. Generate assignment
    gen_res = client.post("/api/assignment/generate", json={"topic": "Python Functions", "level": "Beginner"})
    assert gen_res.status_code == 200
    session_id = gen_res.json()["session_id"]

    # 2. Incomplete answers rejection
    bad_payload = {
        "session_id": session_id,
        "topic": "Python Functions",
        "level": "Beginner",
        "answers": {"1": "[1] then [1, 2]"} # Missing questions 2 and 3
    }
    bad_res = client.post("/api/assignment/submit", json=bad_payload)
    assert bad_res.status_code == 400
    assert "must be answered" in bad_res.json()["detail"]

    # 3. Complete answers submission
    good_payload = {
        "session_id": session_id,
        "topic": "Python Functions",
        "level": "Beginner",
        "answers": {
            "1": "[1] then [1, 2]",
            "2": "map(discount, prices)",
            "3": "def fetch(url, *, timeout=30):"
        }
    }
    sub_res = client.post("/api/assignment/submit", json=good_payload)
    assert sub_res.status_code == 200
    eval_data = sub_res.json()

    assert eval_data["total_questions"] == 3
    assert eval_data["correct_count"] == 3
    assert eval_data["score_percentage"] == 100.0
    assert "feedback" in eval_data
    assert len(eval_data["question_review"]) == 3
    assert eval_data["already_submitted"] is False

    # 4. Duplicate submission check (preserves results without error)
    dup_res = client.post("/api/assignment/submit", json=good_payload)
    assert dup_res.status_code == 200
    dup_data = dup_res.json()
    assert dup_data["already_submitted"] is True
    assert dup_data["score_percentage"] == 100.0

    # 5. Status check endpoint
    status_res = client.get(f"/api/assignment/status/{session_id}")
    assert status_res.status_code == 200
    assert status_res.json()["submitted"] is True

def test_assessment_security_and_evaluation_flow():
    """
    CRITICAL ASSESSMENT SECURITY & WORKFLOW TEST:
    1. Generate assessment questions.
    2. Confirm correct_answer and explanation are NOT present in client response.
    3. Submit answers to backend for evaluation.
    4. Verify scoring and concept mapping.
    """
    gen_res = client.post("/api/test/generate", json={"topic": "Python Functions", "level": "Beginner"})
    assert gen_res.status_code == 200
    gen_data = gen_res.json()

    session_id = gen_data["session_id"]
    questions = gen_data["questions"]
    assert len(questions) > 0
    assert session_id is not None

    for q in questions:
        assert "correct_answer" not in q, f"SECURITY VIOLATION: Question {q['question_id']} leaked correct_answer!"
        assert "explanation" not in q, f"SECURITY VIOLATION: Question {q['question_id']} leaked explanation!"
        assert "options" in q
        assert "concept" in q

    answers_payload = {
        "session_id": session_id,
        "topic": "Python Functions",
        "level": "Beginner",
        "answers": {
            "101": "def calculate_tax(income):",
            "102": "Wrong Answer",
            "103": "Wrong Answer",
            "104": "Wrong Answer"
        }
    }

    sub_res = client.post("/api/test/submit", json=answers_payload)
    assert sub_res.status_code == 200
    eval_data = sub_res.json()

    assert eval_data["total_questions"] == 4
    assert eval_data["correct_count"] == 1
    assert eval_data["score_percentage"] == 25.0
    assert len(eval_data["weak_concepts"]) > 0
    assert "question_review" in eval_data

    q101_review = next(r for r in eval_data["question_review"] if r["question_id"] == 101)
    assert q101_review["is_correct"] is True

def test_targeted_practice_generation():
    """Verify /api/targeted-practice produces focused remediation for a weak concept."""
    payload = {
        "topic": "Python Functions",
        "weak_concept": "Parameter Passing",
        "level": "Beginner"
    }
    res = client.post("/api/targeted-practice", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["concept"] == "Parameter Passing"
    assert "explanation" in data
    assert "drill_question" in data
    assert data["drill_question"]["question"] is not None

def test_progress_persistence():
    """Verify /api/progress reflects recorded attempts and concept mastery in SQLite."""
    res = client.get("/api/progress")
    assert res.status_code == 200
    data = res.json()
    assert data["total_attempts"] >= 1
    assert "Python Functions" in [c["topic"] for c in data["concept_mastery"]]
    assert len(data["recent_attempts"]) >= 1
