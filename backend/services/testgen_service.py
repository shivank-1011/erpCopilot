"""
services/testgen_service.py — Generate structured ERP test cases via Gemini JSON mode.

Why native Gemini SDK here instead of LangChain?
  - Gemini's response_mime_type="application/json" guarantees valid JSON output.
  - This is cleaner than parsing JSON from LangChain's string output.
  - Gives us more control over generation config (temperature, max tokens).
"""
import json
import re
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from prompts.testgen_prompt import TESTGEN_SYSTEM_PROMPT, TESTGEN_USER_TEMPLATE
from config import get_settings
from services.key_manager import key_manager

settings = get_settings()


def _configure_gemini():
    genai.configure(api_key=key_manager.get_key())


def _call_gemini_json(system_prompt: str, user_prompt: str) -> dict:
    """
    Call Gemini with JSON mode enabled.
    Rotates keys if a rate limit or quota exceeded error occurs.
    """
    max_attempts = max(len(key_manager.keys), 1) * 2
    last_exception = None

    for attempt in range(max_attempts):
        try:
            _configure_gemini()

            model = genai.GenerativeModel(
                model_name=settings.gemini_chat_model,
                system_instruction=system_prompt,
            )

            response = model.generate_content(
                user_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                    max_output_tokens=4096,
                ),
            )

            raw_text = response.text.strip()

            # Extra safety: strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)

            return json.loads(raw_text)

        except (ResourceExhausted, Exception) as e:
            # Check if this is a quota or rate-limit issue
            err_msg = str(e).lower()
            is_rate_limit = (
                isinstance(e, ResourceExhausted) or
                "429" in err_msg or
                "quota" in err_msg or
                "resource_exhausted" in err_msg
            )

            if is_rate_limit:
                print(f"[testgen_service] Key exhausted/rate-limited. Rotating from index {key_manager.current_index}...")
                key_manager.rotate_key()
                last_exception = e
            else:
                # Raise other exceptions immediately
                raise

    raise RuntimeError(
        f"Test case generation failed after exhausting all keys. Last error: {last_exception}"
    ) from last_exception



def generate_test_cases(chunk_text: str, source: str = "Unknown source") -> dict:
    """
    Generate structured ERP test cases from a document chunk.

    Args:
        chunk_text: The raw text of the selected document section.
        source:     Human-readable source citation (filename + page).

    Returns:
        Structured dict with keys:
            feature_name, feature_summary,
            positive_tests, negative_tests, edge_cases
    """
    user_prompt = TESTGEN_USER_TEMPLATE.format(
        source=source,
        chunk_text=chunk_text,
    )

    try:
        result = _call_gemini_json(TESTGEN_SYSTEM_PROMPT, user_prompt)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Test case generation failed: {e}") from e

    # Validate minimum structure
    _validate_test_output(result)
    return result


def _validate_test_output(data: dict) -> None:
    """Basic structural validation of Gemini's output."""
    required_keys = ["feature_name", "positive_tests", "negative_tests", "edge_cases"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key in test gen output: '{key}'")

    if not isinstance(data["positive_tests"], list) or len(data["positive_tests"]) == 0:
        raise ValueError("Test gen output must contain at least one positive test.")
