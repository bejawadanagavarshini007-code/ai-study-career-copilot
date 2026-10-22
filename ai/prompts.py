"""
AI Study & Career Copilot — Prompt Architecture
Distinct, dedicated prompt templates for each stage of the learning cycle.
All prompts demand structured JSON output.
"""

EXPLANATION_PROMPT = """
You are an expert technical mentor and computer science educator.
Explain the topic "{topic}" at the "{level}" level.

Your response must be valid JSON in this exact structure:
{{
  "topic": "{topic}",
  "level": "{level}",
  "explanation": "Clear, intuitive 2-3 paragraph conceptual explanation focusing on real-world mechanics and intuition.",
  "key_points": [
    "Key takeaway or rule 1",
    "Key takeaway or rule 2",
    "Key takeaway or rule 3"
  ],
  "examples": [
    {{
      "title": "Descriptive title for example",
      "code": "Concise code or concrete example snippet illustrating the concept",
      "notes": "Brief explanation of how the example operates"
    }}
  ]
}}
Do NOT output markdown backticks or any text outside the JSON object.
"""

PRACTICE_PROMPT = """
You are an interactive tutor.
Generate 3 practice multiple-choice questions for "{topic}" at the "{level}" difficulty level.
Practice questions should help the student learn with immediate explanatory feedback and guiding hints.

Your response must be valid JSON in this exact structure:
{{
  "questions": [
    {{
      "question_id": 1,
      "concept": "Specific sub-concept being practiced (e.g. Return Values, Syntax, Scope)",
      "question": "Clear question text?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Exact text of the correct option",
      "explanation": "Clear explanation of why this option is correct and why other choices are misconceptions.",
      "hint": "A guiding pedagogical clue to help point the student toward the right mental model without giving away the direct answer."
    }}
  ]
}}
Do NOT output markdown backticks or any text outside the JSON object.
"""

ASSIGNMENT_PROMPT = """
You are a senior technical instructor creating a practical assignment.
Generate 3 applied scenario-based assignment questions for "{topic}" at the "{level}" difficulty level.
These questions should test practical problem solving, code analysis, and real-world application.

Your response must be valid JSON in this exact structure:
{{
  "title": "{topic} Practical Assignment",
  "instructions": "Analyze the following practical scenarios and select the most appropriate solution for each.",
  "questions": [
    {{
      "question_id": 1,
      "concept": "Specific concept applied (e.g. Function Composition, Edge Case Handling)",
      "question": "Realistic scenario or problem description with code to analyze?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Exact text of the correct option",
      "explanation": "Detailed step-by-step breakdown of why this option is correct.",
      "hint": "Practical hint to help reason through the scenario."
    }}
  ]
}}
Do NOT output markdown backticks or any text outside the JSON object.
"""

TEST_GENERATION_PROMPT = """
You are a rigorous assessment examiner.
Generate 4 test multiple-choice questions for the topic "{topic}" at the "{level}" level.
IMPORTANT: Each question MUST map to a specific sub-concept under "{topic}" so that performance can be diagnosed.

Your response must be valid JSON in this exact structure:
{{
  "questions": [
    {{
      "question_id": 101,
      "concept": "Specific sub-concept (e.g. Parameter Passing, Default Arguments, Return Semantics)",
      "question": "Precise question testing practical understanding?",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "correct_answer": "Exact text of the correct option",
      "explanation": "Detailed rationale for the correct answer."
    }}
  ]
}}
Do NOT output markdown backticks or any text outside the JSON object.
"""

TARGETED_PRACTICE_PROMPT = """
You are a personalized learning coach.
The student took an assessment on "{topic}" ({level} level) and demonstrated weakness in the specific concept: "{weak_concept}".

Create a targeted remedial lesson to cure this specific misconception and solidify understanding.

Your response must be valid JSON in this exact structure:
{{
  "concept": "{weak_concept}",
  "topic": "{topic}",
  "explanation": "Targeted, crystal-clear explanation addressing why this concept is often confusing and how to master it.",
  "example_title": "Concrete demonstration",
  "example_code": "Snippet demonstrating the correct mental model and how to avoid the common pitfall",
  "example_notes": "Explanation of the code pattern",
  "drill_question": {{
    "question": "A focused drill question strictly testing {weak_concept}?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Exact text of correct option",
    "explanation": "Detailed explanation reinforcing the solution."
  }}
}}
Do NOT output markdown backticks or any text outside the JSON object.
"""
