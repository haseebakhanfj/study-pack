"""
Core AI Workflow Orchestration Pipeline.
Handles API invocation, context propagation, JSON parsing, error retries, and fallback mechanisms.
"""

import json
import re
import os
from typing import Dict, Any, Tuple
from groq import Groq
import prompt

DEFAULT_MODEL = "openai/gpt-oss-120b"

class WorkflowError(Exception):
    """Custom exception class for pipeline stage failures."""
    pass


class StudyPackWorkflow:
    def __init__(self, api_key: str = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API Key is missing. Set GROQ_API_KEY environment variable or pass explicitly.")
        self.client = Groq(api_key=self.api_key)
        self.model = model

    def _call_groq(self, prompt_text: str, max_retries: int = 2) -> Dict[str, Any]:
        """Utility method to execute API calls with retry logic and strict JSON extraction."""
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a precise JSON-only responding assistant."},
                        {"role": "user", "content": prompt_text}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                raw_text = response.choices[0].message.content
                
                # Direct JSON Parse
                return json.loads(raw_text)
            except Exception as err:
                # Attempt regex cleanup if pure JSON parsing fails
                try:
                    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
                except Exception:
                    pass
                
                if attempt == max_retries:
                    raise WorkflowError(f"Stage Execution Failed after {max_retries+1} attempts: {str(err)}")

    # Stage 1: Planning
    def run_planning(self, topic: str, target_audience: str, additional_notes: str) -> Dict[str, Any]:
        p = prompt.PLANNING_PROMPT.format(
            topic=topic,
            target_audience=target_audience,
            additional_notes=additional_notes or "None"
        )
        return self._call_groq(p)

    # Stage 2: Content Generation
    def run_content_generation(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        plan_str = json.dumps(plan_data, indent=2)
        p = prompt.CONTENT_GENERATION_PROMPT.format(plan_context=plan_str)
        return self._call_groq(p)

    # Stage 3: Assessment
    def run_assessment(self, plan_data: Dict[str, Any], content_data: Dict[str, Any]) -> Dict[str, Any]:
        plan_str = json.dumps(plan_data, indent=2)
        content_summary = content_data.get("content_markdown", "")[:2000] # Pass relevant context window
        p = prompt.ASSESSMENT_PROMPT.format(
            plan_context=plan_str,
            content_context=content_summary
        )
        return self._call_groq(p)

    # Stage 4: Review
    def run_review(self, topic: str, target_audience: str, plan_data: Dict[str, Any], content_data: Dict[str, Any], assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        p = prompt.REVIEW_PROMPT.format(
            topic=topic,
            target_audience=target_audience,
            plan_context=json.dumps(plan_data, indent=2),
            content_context=content_data.get("content_markdown", "")[:1500],
            assessment_context=json.dumps(assessment_data, indent=2)[:1500]
        )
        return self._call_groq(p)

    # Stage 5: Refinement
    def run_refinement(self, content_data: Dict[str, Any], review_data: Dict[str, Any]) -> Dict[str, Any]:
        p = prompt.REFINEMENT_PROMPT.format(
            content_context=content_data.get("content_markdown", ""),
            review_context=json.dumps(review_data, indent=2)
        )
        return self._call_groq(p)

    # Orchestrator Workflow Execution
    def generate_full_study_pack(self, topic: str, audience: str, notes: str, status_callback=None) -> Dict[str, Any]:
        """Executes the complete 5-stage sequential workflow with context state passing."""
        context_store = {}

        # 1. Planning
        if status_callback: status_callback("Stage 1/5: Planning study structure...")
        context_store["plan"] = self.run_planning(topic, audience, notes)

        # 2. Content Generation
        if status_callback: status_callback("Stage 2/5: Generating study guide content...")
        context_store["content"] = self.run_content_generation(context_store["plan"])

        # 3. Assessment
        if status_callback: status_callback("Stage 3/5: Formulating assessment questions...")
        context_store["assessment"] = self.run_assessment(context_store["plan"], context_store["content"])

        # 4. Review
        if status_callback: status_callback("Stage 4/5: Reviewing generated material for quality...")
        context_store["review"] = self.run_review(
            topic, audience, context_store["plan"], context_store["content"], context_store["assessment"]
        )

        # 5. Conditional Refinement
        if context_store["review"].get("status") == "NEEDS_REFINEMENT":
            if status_callback: status_callback("Stage 5/5: Applying quality refinements...")
            refinement_res = self.run_refinement(context_store["content"], context_store["review"])
            # Update content markdown with refined material
            context_store["content"]["content_markdown"] = refinement_res.get("refined_content_markdown", context_store["content"]["content_markdown"])
            context_store["refinement_applied"] = True
            context_store["refinement_log"] = refinement_res.get("applied_improvements", [])
        else:
            if status_callback: status_callback("Stage 5/5: Quality check passed! Finalizing pack...")
            context_store["refinement_applied"] = False

        return context_store
