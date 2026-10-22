"""
AI Study & Career Copilot — AI Service Layer
Provides structured AI generation with Google Gemini API and a rich Curated Concept Engine fallback.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import httpx

from ai.prompts import (
    EXPLANATION_PROMPT,
    PRACTICE_PROMPT,
    ASSIGNMENT_PROMPT,
    TEST_GENERATION_PROMPT,
    TARGETED_PRACTICE_PROMPT
)

# --- PYDANTIC SCHEMAS ---

class ExampleModel(BaseModel):
    title: str
    code: str
    notes: str

class ExplanationResponse(BaseModel):
    topic: str
    level: str
    explanation: str
    key_points: List[str]
    examples: List[ExampleModel]

class PracticeQuestionModel(BaseModel):
    question_id: int
    concept: str
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    hint: Optional[str] = None

class PracticeResponse(BaseModel):
    questions: List[PracticeQuestionModel]

class AssignmentQuestionModel(BaseModel):
    question_id: int
    concept: str
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    hint: Optional[str] = None

class AssignmentResponse(BaseModel):
    title: str
    instructions: str
    questions: List[AssignmentQuestionModel]

class TestQuestionModel(BaseModel):
    question_id: int
    concept: str
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class TestQuestionsResponse(BaseModel):
    questions: List[TestQuestionModel]

class DrillQuestionModel(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class TargetedPracticeResponse(BaseModel):
    concept: str
    topic: str
    explanation: str
    example_title: str
    example_code: str
    example_notes: str
    drill_question: DrillQuestionModel


# --- CURATED CONCEPT ENGINE (HIGH QUALITY OFFLINE / RESILIENT FALLBACK) ---

CURATED_TOPICS = {
    "python functions": {
        "explanation": {
            "topic": "Python Functions",
            "level": "Beginner",
            "explanation": "A function in Python is an organized, reusable block of code used to perform a single, related action. Functions provide better modularity for your application and a high degree of code reusing. In Python, functions are first-class citizens, meaning they can be passed as arguments, assigned to variables, and returned from other functions.",
            "key_points": [
                "Defined using the 'def' keyword followed by the function name and parentheses ().",
                "Parameters allow data to be passed into functions; default parameters provide fallback values.",
                "The 'return' statement exits the function and sends a result back; without an explicit return, a function returns None.",
                "Variables declared inside a function have local scope and cannot be accessed outside."
            ],
            "examples": [
                {
                    "title": "Basic Function Definition with Default Argument",
                    "code": "def greet(name, greeting='Hello'):\n    \"\"\"Return a customized greeting string.\"\"\"\n    return f\"{greeting}, {name}!\"\n\nprint(greet('Alice'))              # Output: Hello, Alice!\nprint(greet('Bob', 'Welcome'))     # Output: Welcome, Bob!",
                    "notes": "Demonstrates parameter default fallback and formatted return value."
                },
                {
                    "title": "Multiple Return Values via Tuple Packing",
                    "code": "def calculate_stats(numbers):\n    total = sum(numbers)\n    avg = total / len(numbers)\n    return total, avg\n\ns, a = calculate_stats([10, 20, 30])\nprint(f'Sum: {s}, Average: {a}')",
                    "notes": "Functions can return multiple values separated by commas, automatically packed as a tuple."
                }
            ]
        },
        "practice": [
            {
                "question_id": 1,
                "concept": "Function Definition",
                "question": "Which keyword is used in Python to declare a function?",
                "options": ["function", "def", "func", "define"],
                "correct_answer": "def",
                "explanation": "In Python, 'def' (short for define) is the reserved keyword used to begin a function header.",
                "hint": "Think of a three-letter abbreviation of 'define'."
            },
            {
                "question_id": 2,
                "concept": "Return Values",
                "question": "What is the return value of a Python function that does not include an explicit return statement?",
                "options": ["0", "False", "None", "undefined"],
                "correct_answer": "None",
                "explanation": "Python automatically returns the singleton object 'None' when execution reaches the end of a function without hitting a return statement.",
                "hint": "Python has a special singleton representing the absence of a value."
            },
            {
                "question_id": 3,
                "concept": "Parameter Passing",
                "question": "In the function header 'def connect(host, port=8080):', what is 'port=8080' called?",
                "options": ["A keyword argument", "A default parameter", "A global variable", "A lambda expression"],
                "correct_answer": "A default parameter",
                "explanation": "Parameters defined with values in the header are default parameters. If the caller omits that argument, the default is used.",
                "hint": "It provides a fallback value if no argument is supplied."
            }
        ],
        "assignment": {
            "title": "Python Functions Scenario Assignment",
            "instructions": "Examine each engineering scenario carefully and determine the optimal function implementation.",
            "questions": [
                {
                    "question_id": 1,
                    "concept": "Default Mutable Arguments",
                    "question": "What is the output of calling append_item(1) then append_item(2) on:\ndef append_item(val, items=[]):\n    items.append(val)\n    return items",
                    "options": ["[1] then [2]", "[1] then [1, 2]", "[1, 2] both times", "Raises TypeError"],
                    "correct_answer": "[1] then [1, 2]",
                    "explanation": "Default argument expressions in Python are evaluated once when the function is defined, so a mutable default list is shared across all function calls.",
                    "hint": "Remember that default parameters are evaluated at function definition time, not runtime."
                },
                {
                    "question_id": 2,
                    "concept": "Function Composition & Higher-Order Functions",
                    "question": "You need to apply a discount function to a list of prices using functional style. Which built-in function pairs best with a unary discount function?",
                    "options": ["map(discount, prices)", "filter(discount, prices)", "reduce(prices)", "zip(discount, prices)"],
                    "correct_answer": "map(discount, prices)",
                    "explanation": "The map() function applies a specified transformation function to each item of an iterable and returns an iterator.",
                    "hint": "Think about transforming each element of a collection rather than selecting or aggregating."
                },
                {
                    "question_id": 3,
                    "concept": "Keyword-Only Arguments",
                    "question": "How do you enforce that an argument 'timeout' MUST be passed as a keyword argument in Python?",
                    "options": [
                        "def fetch(url, *, timeout=30):",
                        "def fetch(url, timeout: keyword = 30):",
                        "def fetch(url, [timeout]=30):",
                        "def fetch(url, kw_only(timeout=30)):"
                    ],
                    "correct_answer": "def fetch(url, *, timeout=30):",
                    "explanation": "A bare asterisk '*' in the parameter list marks all following parameters as keyword-only arguments.",
                    "hint": "Python uses a special single symbol in the parameter list to separate positional from keyword-only arguments."
                }
            ]
        },
        "test": [
            {
                "question_id": 101,
                "concept": "Function Definition",
                "question": "Which statement correctly defines a function named 'calculate_tax' taking 'income'?",
                "options": [
                    "def calculate_tax(income):",
                    "function calculate_tax(income) {",
                    "create calculate_tax(income):",
                    "def calculate_tax(income) -> void"
                ],
                "correct_answer": "def calculate_tax(income):",
                "explanation": "Python function definitions must start with 'def', followed by the identifier, parameters in parentheses, and a colon."
            },
            {
                "question_id": 102,
                "concept": "Parameter Passing",
                "question": "What happens if a caller provides only one argument to a function defined as: 'def add(x, y=10):'?",
                "options": [
                    "A TypeError is raised for missing arguments",
                    "x takes the provided value, and y uses 10",
                    "x and y both become 10",
                    "The function returns None without executing"
                ],
                "correct_answer": "x takes the provided value, and y uses 10",
                "explanation": "Because 'y' has a default parameter of 10, supplying only one argument binds it to 'x'."
            },
            {
                "question_id": 103,
                "concept": "Return Values",
                "question": "Consider: def check(val): if val > 0: return 'Positive'. What does check(-5) return?",
                "options": ["'Negative'", "0", "None", "Raises an UnboundLocalError"],
                "correct_answer": "None",
                "explanation": "Since -5 is not > 0, the if branch is skipped and the function implicitly terminates returning None."
            },
            {
                "question_id": 104,
                "concept": "Variable Scope",
                "question": "A variable declared inside a function body without the 'global' keyword has which scope?",
                "options": ["Module scope", "Global scope", "Local scope", "Built-in scope"],
                "correct_answer": "Local scope",
                "explanation": "Variables assigned inside functions are local to that function call and inaccessible from the outer global scope."
            }
        ],
        "targeted": {
            "Parameter Passing": {
                "explanation": "Parameter passing in Python pairs arguments either positionally or by keyword. A common misconception occurs when mixing default parameters or passing mutable objects (like lists). Always ensure required positional parameters come before default parameters, and remember that callers can override defaults when needed.",
                "example_title": "Handling Positional & Default Parameters Safely",
                "example_code": "# Valid parameter ordering:\ndef register_user(username, role='member', is_active=True):\n    return {\"username\": username, \"role\": role, \"active\": is_active}\n\n# Calling positionally:\nu1 = register_user('Alice')\n# Calling with selective keyword override:\nu2 = register_user('Bob', role='admin')",
                "example_notes": "Required parameters like 'username' must precede optional defaults like 'role' and 'is_active'.",
                "drill_question": {
                    "question": "Which of the following function signatures is syntactically INVALID in Python?",
                    "options": [
                        "def search(query, limit=20, offset=0):",
                        "def search(limit=20, query):",
                        "def search(query, *args, limit=20):",
                        "def search(query, limit=20):"
                    ],
                    "correct_answer": "def search(limit=20, query):",
                    "explanation": "In Python, non-default arguments cannot follow default arguments. 'query' must come before 'limit=20'."
                }
            },
            "Return Values": {
                "explanation": "The 'return' statement designates what value is passed back to the caller and instantly halts execution of the function. If no return statement is encountered, Python implicitly returns None. Confusing printing (displaying output to the terminal) with returning (passing data back to code) is a frequent point of friction.",
                "example_title": "Return vs Print Distinction",
                "example_code": "def calculate_discount(price):\n    # Returning allows further computation\n    return price * 0.9\n\nfinal_price = calculate_discount(100)\n# Now we can compute sales tax on final_price\nprint('Final with tax:', final_price * 1.05)",
                "example_notes": "Returning values permits composition; printing does not produce a usable variable.",
                "drill_question": {
                    "question": "What is the value of 'result' after executing: def f(): print('Hello'); result = f()?",
                    "options": ["'Hello'", "None", "0", "undefined"],
                    "correct_answer": "None",
                    "explanation": "'print()' outputs to stdout but does not return a value. Since f() lacks a return statement, result stores None."
                }
            },
            "Variable Scope": {
                "explanation": "Python uses the LEGB rule (Local, Enclosing, Global, Built-in) to resolve variable names. Variables created inside a function exist strictly within its local frame and are destroyed when the function finishes.",
                "example_title": "Local Scope Isolation",
                "example_code": "x = 100 # Global\n\ndef test_scope():\n    x = 42 # Local shadow\n    return x\n\nprint(test_scope()) # Prints 42\nprint(x)            # Prints 100 (global untouched)",
                "example_notes": "Assigning to x inside test_scope creates a new local variable rather than modifying the outer global x.",
                "drill_question": {
                    "question": "If you need a function to modify a variable in the outer global module scope, which keyword is required?",
                    "options": ["outer", "nonlocal", "global", "export"],
                    "correct_answer": "global",
                    "explanation": "The 'global' keyword explicitly informs Python that assignments to the variable should affect the module-level variable."
                }
            }
        }
    },
    "sql joins": {
        "explanation": {
            "topic": "SQL Joins",
            "level": "Intermediate",
            "explanation": "SQL Joins are clauses used to combine rows from two or more tables based on a related column between them. Joins are fundamental to relational database systems (RDBMS) where data is normalized into discrete entities to eliminate redundancy.",
            "key_points": [
                "INNER JOIN returns records that have matching values in both tables.",
                "LEFT JOIN (or LEFT OUTER JOIN) returns all records from the left table, and matched records from the right table.",
                "Unmatched rows in outer joins are filled with NULLs.",
                "The ON clause defines the join predicate condition."
            ],
            "examples": [
                {
                    "title": "INNER JOIN between Customers and Orders",
                    "code": "SELECT orders.order_id, customers.customer_name\nFROM orders\nINNER JOIN customers ON orders.customer_id = customers.customer_id;",
                    "notes": "Retrieves only orders that have a corresponding customer record."
                }
            ]
        },
        "practice": [
            {
                "question_id": 1,
                "concept": "INNER JOIN",
                "question": "Which JOIN returns only rows where there is a match in both tables?",
                "options": ["LEFT JOIN", "INNER JOIN", "FULL OUTER JOIN", "CROSS JOIN"],
                "correct_answer": "INNER JOIN",
                "explanation": "INNER JOIN discards rows from either table that do not satisfy the join predicate.",
                "hint": "Think of the mathematical intersection between two sets."
            },
            {
                "question_id": 2,
                "concept": "LEFT JOIN",
                "question": "If a row in Table A has no matching row in Table B during an A LEFT JOIN B, what appears in Table B's columns?",
                "options": ["Zero (0)", "An empty string", "NULL", "An exception is thrown"],
                "correct_answer": "NULL",
                "explanation": "Unmatched columns from the right-hand table in an outer join are padded with NULL values.",
                "hint": "Relational databases use a special marker to denote the absence of a value."
            },
            {
                "question_id": 3,
                "concept": "Join Predicates",
                "question": "Which keyword specifies the matching condition between two tables in a JOIN clause?",
                "options": ["WHERE", "ON", "USING KEY", "MATCHING"],
                "correct_answer": "ON",
                "explanation": "The 'ON' keyword specifies the join condition that determines which rows correlate between the joined tables.",
                "hint": "It is a short 2-letter keyword placed directly after the joined table name."
            }
        ],
        "assignment": {
            "title": "SQL Relational Joins Scenario Assignment",
            "instructions": "Analyze each database querying scenario and identify the correct relational join structure.",
            "questions": [
                {
                    "question_id": 1,
                    "concept": "Preserving Unmatched Records",
                    "question": "You need a report listing all users along with their recent orders. Users who have never placed an order must still appear in the list. Which JOIN should you use?",
                    "options": ["INNER JOIN", "LEFT JOIN", "CROSS JOIN", "NATURAL JOIN"],
                    "correct_answer": "LEFT JOIN",
                    "explanation": "LEFT JOIN preserves all rows from the primary (left) users table regardless of whether matching order records exist.",
                    "hint": "You want all records from the first table kept intact."
                },
                {
                    "question_id": 2,
                    "concept": "Exclusive Disjoint Sets",
                    "question": "To isolate records that exist in Table A OR Table B, but NOT in both, which join and filter combination is required?",
                    "options": [
                        "INNER JOIN with WHERE A.id = B.id",
                        "FULL OUTER JOIN with IS NULL filter",
                        "CROSS JOIN with DISTINCT",
                        "LEFT JOIN with LIMIT 10"
                    ],
                    "correct_answer": "FULL OUTER JOIN with IS NULL filter",
                    "explanation": "A FULL OUTER JOIN combined with WHERE A.key IS NULL OR B.key IS NULL excludes the intersection.",
                    "hint": "Think of a symmetric difference in set theory."
                },
                {
                    "question_id": 3,
                    "concept": "Combinatorial Generation",
                    "question": "An e-commerce matrix needs to pair every available color with every available clothing size. Which JOIN type produces this Cartesian product?",
                    "options": ["INNER JOIN", "LEFT JOIN", "CROSS JOIN", "RIGHT JOIN"],
                    "correct_answer": "CROSS JOIN",
                    "explanation": "CROSS JOIN produces the Cartesian product of two tables, multiplying each row of Table 1 by every row of Table 2.",
                    "hint": "It computes the full permutation without requiring an ON clause."
                }
            ]
        },
        "test": [
            {
                "question_id": 101,
                "concept": "INNER JOIN",
                "question": "What is the primary characteristic of an INNER JOIN?",
                "options": [
                    "INNER JOIN",
                    "It returns all rows from the left table only",
                    "It duplicates every row",
                    "It returns all rows from both tables unconditionally"
                ],
                "correct_answer": "INNER JOIN",
                "explanation": "INNER JOIN requires both sides to satisfy the ON predicate."
            },
            {
                "question_id": 102,
                "concept": "Outer Joins",
                "question": "When does a FULL OUTER JOIN produce NULL values in the result columns?",
                "options": [
                    "Whenever either table lacks a matching row for the join key",
                    "Never, it raises an error",
                    "Only on primary keys",
                    "Always on all rows"
                ],
                "correct_answer": "Whenever either table lacks a matching row for the join key",
                "explanation": "Unmatched records from either table are padded with NULLs across the missing side."
            },
            {
                "question_id": 103,
                "concept": "Join Predicates",
                "question": "Which SQL clause binds the correlation condition between two joined tables?",
                "options": ["ON", "WHERE ONLY", "GROUP BY", "HAVING"],
                "correct_answer": "ON",
                "explanation": "The ON clause provides the join condition."
            },
            {
                "question_id": 104,
                "concept": "Cartesian Product",
                "question": "What is the mathematical output of a CROSS JOIN without a filter?",
                "options": [
                    "Cartesian product of both tables",
                    "Intersection of both tables",
                    "Union of both tables",
                    "Difference of both tables"
                ],
                "correct_answer": "Cartesian product of both tables",
                "explanation": "A CROSS JOIN produces N x M rows representing all pairings."
            }
        ],
        "targeted": {
            "LEFT JOIN": {
                "explanation": "A LEFT JOIN preserves every row from the left table regardless of whether the right table has a match. When looking for 'missing' or 'unassigned' relationships (e.g., customers who haven't placed an order), you use LEFT JOIN combined with WHERE right_table.id IS NULL.",
                "example_title": "Finding Orphaned Records with LEFT JOIN",
                "example_code": "SELECT c.name\nFROM customers c\nLEFT JOIN orders o ON c.id = o.customer_id\nWHERE o.id IS NULL;",
                "example_notes": "Filters out customers who have orders, leaving only those with NULL order IDs.",
                "drill_question": {
                    "question": "Which WHERE clause finds rows in Table A that have no match in Table B when performing: SELECT * FROM A LEFT JOIN B ON A.id = B.a_id?",
                    "options": ["WHERE B.a_id = 0", "WHERE B.a_id IS NULL", "WHERE B.a_id != A.id", "WHERE B.a_id IS NOT NULL"],
                    "correct_answer": "WHERE B.a_id IS NULL",
                    "explanation": "Because unmatched rows contain NULLs for table B columns, checking IS NULL isolates unmatched rows."
                }
            },
            "Outer Joins": {
                "explanation": "Outer joins (LEFT, RIGHT, FULL) are designed to retain rows that would otherwise be discarded by an INNER JOIN. The key mental model is that missing data from the opposing table is represented as SQL NULL.",
                "example_title": "FULL OUTER JOIN Syntax Pattern",
                "example_code": "SELECT a.name, b.title\nFROM employees a\nFULL OUTER JOIN projects b ON a.project_id = b.id;",
                "example_notes": "Preserves unassigned employees and unclaimed projects simultaneously.",
                "drill_question": {
                    "question": "If Table A has 5 rows and Table B has 0 rows, how many rows does SELECT * FROM A LEFT JOIN B ON A.id = B.id return?",
                    "options": ["0", "5", "10", "Error"],
                    "correct_answer": "5",
                    "explanation": "All 5 rows of Table A are preserved, with NULLs for Table B."
                }
            }
        }
    }
}


def _extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Cleans and extracts JSON payload from LLM responses even if wrapped in markdown blocks.
    """
    cleaned = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if match:
        cleaned = match.group(1).strip()
    return json.loads(cleaned)


async def _call_gemini_api(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Calls Google Gemini API using GEMINI_API_KEY if configured.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            if res.status_code == 200:
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return _extract_json_from_text(raw_text)
    except Exception as e:
        print(f"[AI Service] Gemini API call failed or timed out: {e}. Falling back to Curated Engine.")
    return None


class AIService:
    """
    High-level AI Service integrating Gemini with the resilient Curated Concept Engine.
    """

    @staticmethod
    async def generate_explanation(topic: str, level: str) -> Dict[str, Any]:
        prompt = EXPLANATION_PROMPT.format(topic=topic, level=level)
        result = await _call_gemini_api(prompt)

        if result:
            try:
                validated = ExplanationResponse(**result)
                return validated.model_dump()
            except Exception as e:
                print(f"[AI Service] Validation error on Gemini response: {e}")

        # Fallback to Curated Engine
        topic_lower = topic.strip().lower()
        if topic_lower in CURATED_TOPICS and "explanation" in CURATED_TOPICS[topic_lower]:
            return CURATED_TOPICS[topic_lower]["explanation"]

        # Dynamic high-fidelity fallback for any custom topic
        return {
            "topic": topic,
            "level": level,
            "explanation": f"{topic} is an essential concept in software engineering and modern problem solving. At the {level} level, mastering its fundamental structure, expected inputs/outputs, and underlying mechanics is critical to building scalable and bug-free applications.",
            "key_points": [
                f"Understand the syntax and structural declarations associated with {topic}.",
                f"Distinguish between internal operations and external side effects.",
                f"Observe best practices regarding readability, modularity, and error handling."
            ],
            "examples": [
                {
                    "title": f"Standard Implementation of {topic}",
                    "code": f"# Practical example of {topic} ({level})\ndef process_{topic.lower().replace(' ', '_')}(data):\n    # Process data according to {topic} conventions\n    result = [x for x in data if x is not None]\n    return result\n\noutput = process_{topic.lower().replace(' ', '_')}([1, 2, None, 4])\nprint('Result:', output)",
                    "notes": f"Illustrates safe handling and structured execution for {topic}."
                }
            ]
        }

    @staticmethod
    async def generate_practice_questions(topic: str, level: str) -> Dict[str, Any]:
        prompt = PRACTICE_PROMPT.format(topic=topic, level=level)
        result = await _call_gemini_api(prompt)

        if result:
            try:
                validated = PracticeResponse(**result)
                return validated.model_dump()
            except Exception as e:
                print(f"[AI Service] Practice validation error: {e}")

        # Fallback
        topic_lower = topic.strip().lower()
        if topic_lower in CURATED_TOPICS and "practice" in CURATED_TOPICS[topic_lower]:
            return {"questions": CURATED_TOPICS[topic_lower]["practice"]}

        # Dynamic fallback questions
        return {
            "questions": [
                {
                    "question_id": 1,
                    "concept": f"{topic} Syntax",
                    "question": f"Which statement best describes the primary purpose of {topic}?",
                    "options": [
                        f"To structure and modularize logic related to {topic}",
                        "To bypass system security protocols",
                        "To compile code directly into assembly language",
                        "To delete temporary system logs"
                    ],
                    "correct_answer": f"To structure and modularize logic related to {topic}",
                    "explanation": f"{topic} exists to promote clean organization, maintainability, and reusability."
                },
                {
                    "question_id": 2,
                    "concept": f"{topic} Mechanics",
                    "question": f"What is a recommended practice when working with {topic}?",
                    "options": [
                        "Avoid testing edge cases",
                        "Keep functions and components focused on a single responsibility",
                        "Use hardcoded constants without documentation",
                        "Suppress all error messages silently"
                    ],
                    "correct_answer": "Keep functions and components focused on a single responsibility",
                    "explanation": "Single responsibility leads to predictable behavior and easier debugging."
                }
            ]
        }

    @staticmethod
    async def generate_assignment(topic: str, level: str) -> Dict[str, Any]:
        """
        Generates applied practical assignment questions for the topic and difficulty.
        Note: The return value includes 'correct_answer' which the BACKEND must strip before sending to client!
        """
        prompt = ASSIGNMENT_PROMPT.format(topic=topic, level=level)
        result = await _call_gemini_api(prompt)

        if result:
            try:
                validated = AssignmentResponse(**result)
                return validated.model_dump()
            except Exception as e:
                print(f"[AI Service] Assignment validation error: {e}")

        # Fallback check
        topic_lower = topic.strip().lower()
        if topic_lower in CURATED_TOPICS and "assignment" in CURATED_TOPICS[topic_lower]:
            return CURATED_TOPICS[topic_lower]["assignment"]

        # Dynamic fallback assignment
        return {
            "title": f"{topic} Practical Engineering Assignment",
            "instructions": f"Evaluate the real-world scenarios below and select the most effective solution for {topic}.",
            "questions": [
                {
                    "question_id": 1,
                    "concept": f"{topic} Problem Solving",
                    "question": f"A production service utilizing {topic} encounters unexpected behavior during peak load. Which architectural pattern prevents state pollution?",
                    "options": [
                        "Enforce pure, stateless operations without shared global mutations",
                        "Store all transient state in un-synchronized global variables",
                        "Restart the process after every single request",
                        "Disable exception logging to improve latency"
                    ],
                    "correct_answer": "Enforce pure, stateless operations without shared global mutations",
                    "explanation": "Stateless designs isolate execution frames and prevent concurrent race conditions.",
                    "hint": "Consider isolation and idempotency in distributed systems."
                },
                {
                    "question_id": 2,
                    "concept": f"{topic} Error Handling",
                    "question": f"When handling edge cases in {topic}, how should unexpected inputs be reported back to upstream callers?",
                    "options": [
                        "Raise descriptive domain-specific exceptions or return validated result types",
                        "Silently return 0 or None without explanation",
                        "Crash the host operating system",
                        "Output print statements and continue execution blindly"
                    ],
                    "correct_answer": "Raise descriptive domain-specific exceptions or return validated result types",
                    "explanation": "Descriptive exceptions inform callers of preconditions that were violated.",
                    "hint": "Think about clear contract boundaries and debuggability."
                },
                {
                    "question_id": 3,
                    "concept": f"{topic} Maintainability",
                    "question": f"Which refactoring practice yields the greatest improvement in testability for {topic}?",
                    "options": [
                        "Decomposing complex monolithic functions into small, single-purpose units",
                        "Combining all modules into a single 5000-line file",
                        "Removing all unit tests to speed up CI/CD",
                        "Hardcoding database connection strings inside function bodies"
                    ],
                    "correct_answer": "Decomposing complex monolithic functions into small, single-purpose units",
                    "explanation": "Small, single-responsibility units are significantly easier to mock, verify, and reason about.",
                    "hint": "Refer to the Single Responsibility Principle (SRP)."
                }
            ]
        }

    @staticmethod
    async def generate_test_questions(topic: str, level: str) -> Dict[str, Any]:
        """
        Generates assessment questions. Note: The return value includes 'correct_answer'
        which the BACKEND must strip before sending to the client!
        """
        prompt = TEST_GENERATION_PROMPT.format(topic=topic, level=level)
        result = await _call_gemini_api(prompt)

        if result:
            try:
                validated = TestQuestionsResponse(**result)
                return validated.model_dump()
            except Exception as e:
                print(f"[AI Service] Test validation error: {e}")

        # Fallback
        topic_lower = topic.strip().lower()
        if topic_lower in CURATED_TOPICS and "test" in CURATED_TOPICS[topic_lower]:
            return {"questions": CURATED_TOPICS[topic_lower]["test"]}

        # Dynamic fallback
        return {
            "questions": [
                {
                    "question_id": 101,
                    "concept": f"{topic} Definition",
                    "question": f"In {topic}, what is the foundational building block for establishing behavior?",
                    "options": [
                        "Defining modular and deterministic logic",
                        "Disabling all variable types",
                        "Executing scripts without error handlers",
                        "Writing infinite loops"
                    ],
                    "correct_answer": "Defining modular and deterministic logic",
                    "explanation": "Modularity and determinism ensure repeatable and testable operations."
                },
                {
                    "question_id": 102,
                    "concept": f"{topic} Execution Flow",
                    "question": f"What occurs when an unexpected input is provided to {topic} without validation?",
                    "options": [
                        "The system handles it automatically without code",
                        "An exception or unexpected state is likely triggered",
                        "The input is silently deleted",
                        "Hardware memory expands automatically"
                    ],
                    "correct_answer": "An exception or unexpected state is likely triggered",
                    "explanation": "Unvalidated input causes runtime errors, making validation necessary."
                },
                {
                    "question_id": 103,
                    "concept": f"{topic} Performance",
                    "question": f"Which factor most directly affects execution efficiency in {topic}?",
                    "options": [
                        "Algorithmic complexity (time and space)",
                        "The number of comments in the code",
                        "The monitor resolution used by the developer",
                        "Variable name lengths"
                    ],
                    "correct_answer": "Algorithmic complexity (time and space)",
                    "explanation": "Time and space complexity govern performance characteristics at scale."
                }
            ]
        }

    @staticmethod
    async def generate_targeted_practice(topic: str, weak_concept: str, level: str) -> Dict[str, Any]:
        prompt = TARGETED_PRACTICE_PROMPT.format(topic=topic, weak_concept=weak_concept, level=level)
        result = await _call_gemini_api(prompt)

        if result:
            try:
                validated = TargetedPracticeResponse(**result)
                return validated.model_dump()
            except Exception as e:
                print(f"[AI Service] Targeted practice validation error: {e}")

        # Fallback check in Curated Topics
        topic_lower = topic.strip().lower()
        if topic_lower in CURATED_TOPICS:
            targeted_map = CURATED_TOPICS[topic_lower].get("targeted", {})
            for concept_key, concept_data in targeted_map.items():
                if concept_key.lower() in weak_concept.lower() or weak_concept.lower() in concept_key.lower():
                    return {
                        "concept": weak_concept,
                        "topic": topic,
                        "explanation": concept_data["explanation"],
                        "example_title": concept_data["example_title"],
                        "example_code": concept_data["example_code"],
                        "example_notes": concept_data["example_notes"],
                        "drill_question": concept_data["drill_question"]
                    }

        # Dynamic fallback drill
        return {
            "concept": weak_concept,
            "topic": topic,
            "explanation": f"The concept '{weak_concept}' often trips learners up because of subtleties in execution rules and state handling. The key mental model is to trace how values flow through this step sequentially before reaching the final output.",
            "example_title": f"Reinforcing {weak_concept}",
            "example_code": f"# Focus drill for: {weak_concept}\ndef reinforce_{weak_concept.lower().replace(' ', '_')}(param):\n    # 1. Validate boundary conditions\n    if param is None:\n        return 'Fallback'\n    # 2. Correctly apply {weak_concept} logic\n    return f'Mastered: {{param}}'\n\nprint(reinforce_{weak_concept.lower().replace(' ', '_')}('Success'))",
            "example_notes": f"Notice how explicit checks prevent the common misconception associated with {weak_concept}.",
            "drill_question": {
                "question": f"Which rule directly helps avoid bugs when implementing '{weak_concept}'?",
                "options": [
                    "Checking assumptions and verifying state transitions",
                    "Ignoring edge cases completely",
                    "Randomly changing parameter values",
                    "Never testing the function"
                ],
                "correct_answer": "Checking assumptions and verifying state transitions",
                "explanation": "Verifying state transitions is the most reliable way to prevent bugs in this concept."
            }
        }
