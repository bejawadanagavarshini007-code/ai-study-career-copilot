"""
Comprehensive End-to-End Test Suite for AI Study & Career Copilot Redesign.
Validates the complete 6-stage closed learning cycle:
Learn -> Practice -> Assignment -> Assessment -> Results -> Targeted Practice
Plus static asset validation, empty state checks, and edge cases.
"""

import pytest
from starlette.testclient import TestClient
from backend.app import app
from database.db import init_db

client = TestClient(app)

def setup_module():
    init_db()

def test_static_assets_and_markup_structure():
    """Verify HTML, CSS, and JS files are served and contain the redesigned UI elements."""
    # 1. HTML structure
    html_res = client.get("/")
    assert html_res.status_code == 200
    html = html_res.text
    
    # Check left sidebar and brand (Image 1)
    assert 'class="app-sidebar"' in html
    assert 'OptiMind' in html
    assert 'class="nav-item"' in html
    assert 'id="nav-dashboard"' in html
    assert 'id="nav-assignment"' in html
    
    # Check topbar
    assert 'id="topbar-search-input"' in html
    assert 'id="topbar-topic-label"' in html
    
    # Check Hero card (Image 1)
    assert 'class="lms-hero-card"' in html
    assert 'Enhance your learning with AI' in html
    assert 'class="hero-topic-form"' in html
    
    # Check Course cards & Activity chart
    assert 'class="course-cards-grid"' in html
    assert 'class="activity-bars-container"' in html
    assert 'id="activity-empty-state"' in html
    
    # Check Schedule panel & Calendar strip (Image 1)
    assert 'class="app-schedule-panel"' in html
    assert 'id="calendar-days-strip"' in html
    
    # Check Stage workspace & Dark Curriculum drawer (Image 2)
    assert 'id="stage-workspace"' in html
    assert 'class="curriculum-drawer"' in html
    assert 'id="curriculum-step-learn"' in html
    assert 'id="curriculum-step-practice"' in html
    assert 'id="curriculum-step-assignment"' in html
    assert 'id="curriculum-step-test"' in html
    assert 'id="curriculum-step-results"' in html
    assert 'id="curriculum-step-targeted"' in html
    
    # Check Practice stepper & completion card
    assert 'id="practice-stepper-bar"' in html
    assert 'id="practice-container"' in html
    assert 'id="practice-completion-card"' in html
    assert 'id="btn-practice-to-assignment"' in html
    
    # Check Assignment elements
    assert 'id="assignment-questions-container"' in html
    assert 'id="btn-submit-assignment"' in html
    assert 'id="assignment-results-container"' in html
    
    # 2. CSS verification
    css_res = client.get("/style.css")
    assert css_res.status_code == 200
    css = css_res.text
    assert "--primary: #6366f1;" in css
    assert "--accent-purple: #7c3aed;" in css
    assert "--bg-drawer: #181b26;" in css
    assert ".curriculum-drawer" in css
    assert ".option-btn" in css
    assert ".lms-hero-card" in css

    # 3. JS verification
    js_res = client.get("/script.js")
    assert js_res.status_code == 200
    js = js_res.text
    assert "advancePracticeStepper" in js
    assert "showPracticeCompletion" in js
    assert "submitPracticeAnswer" in js
    assert "submitAssignment" in js
    assert "updateCurriculumDrawer" in js
    assert "renderCalendarStrip" in js

def test_full_learning_cycle_sql_joins():
    """
    Simulate full user journey for 'SQL Joins' (Intermediate):
    1. Learn: fetch explanation
    2. Practice: fetch questions with hints
    3. Assignment: generate, test validation on incomplete answers, submit correct answers
    4. Assessment: generate secure exam, submit with 1 wrong answer to isolate weak concept
    5. Targeted Practice: generate remediation for that isolated weak concept
    6. Progress: confirm persistence in database
    """
    topic = "SQL Joins"
    level = "Intermediate"

    # Stage 1: Learn
    learn_res = client.post("/api/learn", json={"topic": topic, "level": level})
    assert learn_res.status_code == 200
    learn_data = learn_res.json()
    assert learn_data["topic"] == topic
    assert len(learn_data["examples"]) >= 1

    # Stage 2: Practice
    practice_res = client.post("/api/practice", json={"topic": topic, "level": level})
    assert practice_res.status_code == 200
    p_questions = practice_res.json()["questions"]
    assert len(p_questions) >= 2
    for pq in p_questions:
        assert pq["hint"] != ""
        assert pq["explanation"] != ""

    # Stage 3: Assignment
    assign_gen_res = client.post("/api/assignment/generate", json={"topic": topic, "level": level})
    assert assign_gen_res.status_code == 200
    assign_data = assign_gen_res.json()
    assign_session_id = assign_data["session_id"]
    a_questions = assign_data["questions"]
    assert len(a_questions) == 3

    # 3a. Incomplete submission validation
    bad_submit = client.post("/api/assignment/submit", json={
        "session_id": assign_session_id,
        "topic": topic,
        "level": level,
        "answers": {"1": "Some answer"} # missing 2 and 3
    })
    assert bad_submit.status_code == 400

    # 3b. Complete submission
    good_submit = client.post("/api/assignment/submit", json={
        "session_id": assign_session_id,
        "topic": topic,
        "level": level,
        "answers": {
            "1": "LEFT JOIN",
            "2": "FULL OUTER JOIN with IS NULL filter",
            "3": "CROSS JOIN"
        }
    })
    assert good_submit.status_code == 200
    eval_res = good_submit.json()
    assert eval_res["score_percentage"] == 100.0
    assert eval_res["already_submitted"] is False

    # 3c. Duplicate submission check
    dup_submit = client.post("/api/assignment/submit", json={
        "session_id": assign_session_id,
        "topic": topic,
        "level": level,
        "answers": {
            "1": "LEFT JOIN",
            "2": "FULL OUTER JOIN with IS NULL filter",
            "3": "CROSS JOIN"
        }
    })
    assert dup_submit.status_code == 200
    assert dup_submit.json()["already_submitted"] is True

    # Stage 4: Assessment
    test_gen_res = client.post("/api/test/generate", json={"topic": topic, "level": level})
    assert test_gen_res.status_code == 200
    test_session = test_gen_res.json()
    test_session_id = test_session["session_id"]
    test_questions = test_session["questions"]
    assert len(test_questions) == 4

    # Submit test with deliberate mistake to trigger weak concept isolation
    test_submit = client.post("/api/test/submit", json={
        "session_id": test_session_id,
        "topic": topic,
        "level": level,
        "answers": {
            "101": "INNER JOIN", # Correct
            "102": "Wrong Answer", # Incorrect (Outer Joins)
            "103": "ON", # Correct
            "104": "Cartesian product of both tables" # Correct
        }
    })
    assert test_submit.status_code == 200
    test_results = test_submit.json()
    assert test_results["correct_count"] == 3
    assert test_results["score_percentage"] == 75.0
    assert len(test_results["weak_concepts"]) >= 1
    weak_concept = test_results["weak_concepts"][0]

    # Stage 5: Results verified through response fields
    assert "concept_analysis" in test_results
    assert "question_review" in test_results

    # Stage 6: Targeted Remediation for the isolated weak concept
    target_res = client.post("/api/targeted-practice", json={
        "topic": topic,
        "weak_concept": weak_concept,
        "level": level
    })
    assert target_res.status_code == 200
    target_data = target_res.json()
    assert target_data["concept"] == weak_concept
    assert "explanation" in target_data
    assert "drill_question" in target_data

    # Verify persistent progress
    prog_res = client.get("/api/progress")
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data["total_attempts"] >= 1
    assert any(c["topic"] == topic for c in prog_data["concept_mastery"])
