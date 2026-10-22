"""
AI Study & Career Copilot — Database Layer
SQLite persistence for test sessions, secure answer keys, test attempts, concept mastery, and user progress.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "copilot.db")

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[str] = None):
    """
    Initializes database schema if tables do not exist.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Table 1: Test Sessions (Secure backend storage for generated test questions and correct answers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_sessions (
        session_id TEXT PRIMARY KEY,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        questions_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table 2: Test Attempts (Scores and history)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        total_questions INTEGER NOT NULL,
        correct_count INTEGER NOT NULL,
        score_percentage REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table 3: Attempt Answers (Detailed per-question answers and concept tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attempt_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        concept TEXT NOT NULL,
        user_answer TEXT,
        correct_answer TEXT NOT NULL,
        is_correct INTEGER NOT NULL,
        FOREIGN KEY (attempt_id) REFERENCES test_attempts (id) ON DELETE CASCADE
    )
    """)

    # Table 4: Concept Mastery (Cumulative concept tracking for personalization)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS concept_mastery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        concept TEXT NOT NULL,
        times_tested INTEGER DEFAULT 0,
        times_correct INTEGER DEFAULT 0,
        last_status TEXT DEFAULT 'Needs Practice',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(topic, concept)
    )
    """)

    # Table 5: Assignment Sessions (Secure backend storage for assignment questions & answer keys)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignment_sessions (
        session_id TEXT PRIMARY KEY,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        title TEXT NOT NULL,
        instructions TEXT NOT NULL,
        questions_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table 6: Assignment Submissions (Records submitted assignments, prevents duplicates, preserves state)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignment_submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        total_questions INTEGER NOT NULL,
        correct_count INTEGER NOT NULL,
        score_percentage REAL NOT NULL,
        answers_json TEXT NOT NULL,
        review_json TEXT NOT NULL,
        feedback TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def save_test_session(session_id: str, topic: str, difficulty: str, questions: List[Dict[str, Any]], db_path: Optional[str] = None):
    """
    Saves the full test session (including secret correct answers) on the backend.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO test_sessions (session_id, topic, difficulty, questions_json) VALUES (?, ?, ?, ?)",
        (session_id, topic, difficulty, json.dumps(questions))
    )
    conn.commit()
    conn.close()

def get_test_session(session_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves the stored test session with the answer key.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "session_id": row["session_id"],
        "topic": row["topic"],
        "difficulty": row["difficulty"],
        "questions": json.loads(row["questions_json"]),
        "created_at": row["created_at"]
    }

def save_assignment_session(session_id: str, topic: str, difficulty: str, title: str, instructions: str, questions: List[Dict[str, Any]], db_path: Optional[str] = None):
    """
    Saves an assignment session (with secret correct answers) on the backend.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO assignment_sessions (session_id, topic, difficulty, title, instructions, questions_json) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, topic, difficulty, title, instructions, json.dumps(questions))
    )
    conn.commit()
    conn.close()

def get_assignment_session(session_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves the stored assignment session with the answer key.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assignment_sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "session_id": row["session_id"],
        "topic": row["topic"],
        "difficulty": row["difficulty"],
        "title": row["title"],
        "instructions": row["instructions"],
        "questions": json.loads(row["questions_json"]),
        "created_at": row["created_at"]
    }

def save_assignment_submission(
    session_id: str,
    topic: str,
    difficulty: str,
    total_questions: int,
    correct_count: int,
    score_percentage: float,
    answers: Dict[str, str],
    review: List[Dict[str, Any]],
    feedback: str,
    db_path: Optional[str] = None
) -> int:
    """
    Saves an evaluated assignment submission, preventing duplicate submissions and preserving state.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO assignment_submissions 
        (session_id, topic, difficulty, total_questions, correct_count, score_percentage, answers_json, review_json, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id, topic, difficulty, total_questions, correct_count, score_percentage,
            json.dumps(answers), json.dumps(review), feedback
        )
    )
    sub_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sub_id

def get_assignment_submission(session_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves a past assignment submission if it already exists.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assignment_submissions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "session_id": row["session_id"],
        "topic": row["topic"],
        "difficulty": row["difficulty"],
        "total_questions": row["total_questions"],
        "correct_count": row["correct_count"],
        "score_percentage": row["score_percentage"],
        "answers": json.loads(row["answers_json"]),
        "review": json.loads(row["review_json"]),
        "feedback": row["feedback"],
        "created_at": row["created_at"]
    }

def record_attempt_and_mastery(
    session_id: str,
    topic: str,
    difficulty: str,
    total_questions: int,
    correct_count: int,
    score_percentage: float,
    answers_review: List[Dict[str, Any]],
    db_path: Optional[str] = None
) -> int:
    """
    Records an assessment attempt, logs question answers, and updates concept mastery metrics.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Insert Attempt
    cursor.execute(
        """
        INSERT INTO test_attempts (session_id, topic, difficulty, total_questions, correct_count, score_percentage)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session_id, topic, difficulty, total_questions, correct_count, score_percentage)
    )
    attempt_id = cursor.lastrowid

    # 2. Insert Answers & Update Concept Mastery
    for ans in answers_review:
        cursor.execute(
            """
            INSERT INTO attempt_answers (attempt_id, question_id, concept, user_answer, correct_answer, is_correct)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                ans["question_id"],
                ans["concept"],
                ans.get("user_answer", ""),
                ans["correct_answer"],
                1 if ans["is_correct"] else 0
            )
        )

        # Update Concept Mastery
        concept = ans["concept"]
        is_corr = 1 if ans["is_correct"] else 0

        cursor.execute("SELECT id, times_tested, times_correct FROM concept_mastery WHERE topic = ? AND concept = ?", (topic, concept))
        existing = cursor.fetchone()

        if existing:
            new_tested = existing["times_tested"] + 1
            new_correct = existing["times_correct"] + is_corr
            acc = (new_correct / new_tested) * 100
            status = 'Mastered' if acc >= 75 else 'Needs Practice'
            cursor.execute(
                """
                UPDATE concept_mastery 
                SET times_tested = ?, times_correct = ?, last_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_tested, new_correct, status, existing["id"])
            )
        else:
            status = 'Mastered' if is_corr == 1 else 'Needs Practice'
            cursor.execute(
                """
                INSERT INTO concept_mastery (topic, concept, times_tested, times_correct, last_status)
                VALUES (?, ?, 1, ?, ?)
                """,
                (topic, concept, is_corr, status)
            )

    conn.commit()
    conn.close()
    return attempt_id

def get_progress_data(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Aggregates learning progress across all topics and assessments.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Total attempts & average score
    cursor.execute("SELECT COUNT(*) as total, AVG(score_percentage) as avg_score FROM test_attempts")
    stats = cursor.fetchone()
    total_attempts = stats["total"] if stats else 0
    avg_score = stats["avg_score"] if (stats and stats["avg_score"] is not None) else 0.0

    # Distinct topics studied
    cursor.execute("SELECT COUNT(DISTINCT topic) as topic_count FROM test_attempts")
    topic_res = cursor.fetchone()
    topics_studied = topic_res["topic_count"] if topic_res else 0

    # Recent attempts
    cursor.execute(
        "SELECT id, topic, difficulty, total_questions, correct_count, score_percentage, created_at FROM test_attempts ORDER BY id DESC LIMIT 5"
    )
    recent_rows = cursor.fetchall()
    recent_attempts = [dict(r) for r in recent_rows]

    # Concept Mastery
    cursor.execute(
        "SELECT topic, concept, times_tested, times_correct, last_status FROM concept_mastery ORDER BY topic, concept"
    )
    concept_rows = cursor.fetchall()

    strong_concepts = []
    weak_concepts = []
    concept_matrix = []

    for c in concept_rows:
        tested = c["times_tested"]
        correct = c["times_correct"]
        accuracy = (correct / tested * 100) if tested > 0 else 0
        item = {
            "topic": c["topic"],
            "concept": c["concept"],
            "tested": tested,
            "correct": correct,
            "accuracy": round(accuracy, 1),
            "status": c["last_status"]
        }
        concept_matrix.append(item)
        if accuracy >= 75:
            strong_concepts.append(c["concept"])
        else:
            weak_concepts.append(c["concept"])

    conn.close()

    return {
        "topics_studied": topics_studied,
        "total_attempts": total_attempts,
        "average_score": round(avg_score, 1),
        "strong_concepts": list(set(strong_concepts)),
        "weak_concepts": list(set(weak_concepts)),
        "concept_mastery": concept_matrix,
        "recent_attempts": recent_attempts
    }

# Automatically initialize database when module is imported
init_db()
