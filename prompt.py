"""
Prompts for each stage of the AI Study Pack generation workflow.
Ensures JSON string outputs for structured parsing and downstream context passing.
"""

PLANNING_PROMPT = """
You are an expert AI Instructional Designer.
Analyze the following user input and construct a multi-step study plan tailored to the target audience.

TOPIC: {topic}
TARGET AUDIENCE / LEVEL: {target_audience}
ADDITIONAL REQUIREMENTS: {additional_notes}

Return your response strictly as a JSON object matching this structure:
{{
    "title": "Module Title",
    "target_level": "Audience Level",
    "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
    "key_concepts": ["Concept 1", "Concept 2", "Concept 3"],
    "suggested_structure": [
        {{"section": "1. Core Principles", "summary": "Brief scope"}},
        {{"section": "2. Practical Applications", "summary": "Brief scope"}}
    ]
}}
"""

CONTENT_GENERATION_PROMPT = """
You are a master educator creating comprehensive study guide content based on a structured plan.

STUDY PLAN CONTEXT:
{plan_context}

Generate a clear, highly detailed study guide. Use Markdown for clear hierarchy, bullet points, code blocks/formulas if relevant, and bold text for key terms.

Return your response strictly as a JSON object matching this structure:
{{
    "content_markdown": "# Study Guide Title\\n\\n## Section 1...",
    "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"]
}}
"""

ASSESSMENT_PROMPT = """
You are an expert exam author. Create an assessment based directly on the provided study guide and plan.

STUDY PLAN:
{plan_context}

STUDY CONTENT SUMMARY:
{content_context}

Generate 3-5 high-quality multiple-choice questions (MCQs) and 2 short reflection questions.

Return your response strictly as a JSON object matching this structure:
{{
    "multiple_choice": [
        {{
            "id": 1,
            "question": "Question text?",
            "options": ["A) Opt 1", "B) Opt 2", "C) Opt 3", "D) Opt 4"],
            "correct_answer": "A) Opt 1",
            "explanation": "Why this is correct."
        }}
    ],
    "reflection_questions": [
        "1. Reflection prompt one?",
        "2. Reflection prompt two?"
    ]
}}
"""

REVIEW_PROMPT = """
You are an AI Quality Assurance Reviewer evaluating a generated Study Pack.

INPUT CRITERIA:
- Target Topic/Audience: {topic} / {target_audience}

GENERATED CONTENT TO REVIEW:
--- PLAN ---
{plan_context}
--- CONTENT ---
{content_context}
--- ASSESSMENT ---
{assessment_context}

Evaluate for clarity, accuracy, pedagogical alignment, and completeness.
Determine if the study pack is APPROVED as-is, or NEEDS_REFINEMENT.

Return your response strictly as a JSON object matching this structure:
{{
    "status": "APPROVED" or "NEEDS_REFINEMENT",
    "quality_score": 85,
    "strengths": ["Strength 1", "Strength 2"],
    "critiques": ["Critique 1", "Critique 2"],
    "refinement_instructions": "Provide actionable fixes if NEEDS_REFINEMENT, otherwise leave empty."
}}
"""

REFINEMENT_PROMPT = """
You are an AI Content Refiner. Rewrite and perfect the study guide content and assessment based on the quality review feedback.

ORIGINAL CONTENT:
{content_context}

REVIEW FEEDBACK & INSTRUCTIONS:
{review_context}

Produce an updated, higher-quality study guide markdown.

Return your response strictly as a JSON object matching this structure:
{{
    "refined_content_markdown": "# Fully Refined Study Guide\\n\\n...",
    "applied_improvements": ["Fix 1 applied", "Fix 2 applied"]
}}
"""
