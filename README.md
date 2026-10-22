# AI Study & Career Copilot

An AI-powered personalized learning platform engineered around the closed-loop learning cycle:

$$\textbf{Learn} \longrightarrow \textbf{Practice} \longrightarrow \textbf{Assignment} \longrightarrow \textbf{Assessment (Test)} \longrightarrow \textbf{Analyze} \longrightarrow \textbf{Improve} \longrightarrow \textbf{Test Again}$$

AI Study & Career Copilot acts as an active technical tutor and assessment examiner that isolates knowledge gaps down to specific sub-concepts, generates targeted remedial lessons, and measures persistent improvement.

---

## Key Features

1. **Structured Learning**: Conceptual breakdowns with real-world context, key takeaways, and copy-pasteable code examples.
2. **Interactive Practice with Hints**:
   - Individual **Submit Answer** button per practice question.
   - Immediate validation displaying correctness, explanations, and pedagogical hints.
   - Sequential progression to the next question.
   - Practice completion summary with direct progression to Assignment.
3. **Applied Practical Assignment**:
   - Scenario-based engineering questions testing practical decision making.
   - **Submit Assignment** button with validation requiring all answers before submission.
   - Instant calculation of final score, percentage, and qualitative feedback.
   - Duplicate submission prevention and persistent state preservation when navigating Back and forth.
4. **Secure Assessment Engine**:
   - **Zero Answer Leakage**: Correct answers are stored strictly on the server database; the client never receives answer keys before submission.
   - **Concept Mapping**: Every assessment question is mapped to a granular sub-concept (e.g., *Function Definition*, *Parameter Passing*, *Return Values*, *Variable Scope*).
5. **Enforced Progression & Bidirectional Navigation**:
   - Accessible **Back** and **Next** buttons on every screen.
   - Progression guards prevent skipping required practice and assignment submission steps.
6. **Diagnostic Personalization & Weak-Area Detection**: Automatically isolates concepts where accuracy drops below 75%, generating targeted drills and explanatory mini-lessons to cure misconceptions.
7. **Persistent Progress Matrix**: SQLite database tracks total attempts, average scores, and cumulative concept mastery over time.
8. **Dual-Mode AI Resilience**:
   - Direct integration with Google Gemini API via `GEMINI_API_KEY`.
   - Built-in **Curated Concept Engine** ensuring complete, rich functionality out-of-the-box even without an external API key or network connection.

---

## System Architecture

```text
                                 LEARNER
                                    │
                                    ↓
        ┌────────────────────────────────────────────────────────┐
        │                  FRONTEND (SPA)                        │
        │   HTML5 • Modern CSS (Custom Properties) • Vanilla JS  │
        │   Dashboard • Learn • Practice • Assignment • Test     │
        │             Results • Targeted Practice • Progress     │
        └───────────────────────────┬────────────────────────────┘
                                    │  REST HTTP
                                    ↓
        ┌────────────────────────────────────────────────────────┐
        │               BACKEND (Python / FastAPI)               │
        │              Central Application Controller            │
        │  Routes • Input Validation • Pydantic • Error Handling │
        └───────────────┬────────────────────────┬───────────────┘
                        │                        │
                        ↓                        ↓
        ┌────────────────────────┐      ┌────────────────────────┐
        │       AI SERVICE       │      │   DATABASE (SQLite)    │
        │    Gemini 2.5 / 1.5    │      │  Test & Assignment     │
        │           OR           │      │    Sessions (Keys)     │
        │ Curated Concept Engine │      │    Submissions & Scores│
        │ (Structured JSON Fall) │      │    Concept Mastery     │
        └────────────────────────┘      └────────────────────────┘
```

---

## Directory Structure

```text
ai-study-career-copilot/
├── ai/
│   ├── prompts.py          # Structured JSON prompts for Learn, Practice, Assignment, Test, Remediation
│   └── service.py          # Pydantic schemas, Gemini API caller & Curated Concept Engine
├── backend/
│   ├── app.py              # FastAPI server entrypoint & static frontend mount
│   └── routes/
│       └── learning.py     # Endpoints for Learn, Practice, Assignment, Test, Remediation & Progress
├── database/
│   ├── db.py               # SQLite schema, session keys, attempts, concept mastery
│   └── copilot.db          # Auto-generated SQLite persistence
├── frontend/
│   ├── index.html          # Semantic HTML layout with 8 core learning views
│   ├── style.css           # Modern dark-mode responsive design system
│   └── script.js           # Client controller, state machine, and API client
├── tests/
│   └── test_api.py         # Automated pytest suite verifying security, assignment & workflows
├── requirements.txt        # Project dependencies
├── run.bat                 # One-click Windows batch launcher
├── run.ps1                 # PowerShell launcher
├── .gitignore              # Ignores bytecode, databases, environment files
└── README.md               # Master documentation and run guide
```

---

## API Specification

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check and learning cycle status |
| `/api/learn` | `POST` | Generates conceptual breakdown, rules, and code patterns |
| `/api/practice` | `POST` | Returns practice questions with explanations and guiding hints |
| `/api/assignment/generate` | `POST` | Generates scenario-based assignment questions with isolated answer keys |
| `/api/assignment/submit` | `POST` | Validates required answers, scores assignment, provides qualitative feedback, prevents duplicates |
| `/api/assignment/status/{id}` | `GET` | Retrieves existing assignment submission to preserve state on navigation |
| `/api/test/generate` | `POST` | Creates assessment session; **safely strips answers from client payload** |
| `/api/test/submit` | `POST` | Evaluates answers, calculates score, maps weak concepts, updates DB |
| `/api/targeted-practice` | `POST` | Generates focused lesson and drill targeting a specific weak concept |
| `/api/progress` | `GET` | Returns cumulative stats, concept mastery matrix, and attempt history |

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed
- Pip package manager

### 2. Installation
Navigate to the project root and install required packages:
```bash
pip install -r requirements.txt
```

### 3. (Optional) Configure Gemini API
Set your Gemini API key in your environment if you want live dynamic LLM generation for arbitrary topics:
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```
*(Note: If omitted, the application seamlessly uses the built-in Curated Concept Engine).*

### 4. Start the Application
Run the one-click launcher or terminal command:
```bash
python backend/app.py
```
Or double-click `run.bat`.

Open your browser at:
```text
http://127.0.0.1:8000
```

---

## Verification & Automated Testing

To run the automated test suite verifying Practice, Assignment validation, Assessment security, scoring, and persistence:
```bash
python -m pytest tests/test_api.py -v
```

All 9 test suites verify:
- Server and frontend delivery
- Topic explanation structure
- Practice questions with hints and immediate feedback
- Assignment generation without answer leakage
- Assignment submission validation (rejects incomplete answers, calculates score, prevents duplicate submissions)
- Assessment answer isolation and secure evaluation
- Remedial drill generation
- SQLite persistence of mastery metrics
