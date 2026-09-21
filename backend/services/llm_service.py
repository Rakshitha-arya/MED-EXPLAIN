"""LLM service abstraction for prompt formatting, grounding, and GenAI provider execution."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

SYSTEM_INSTRUCTION = """You are an educational medical assistant for the MedExplain platform.

STRICT GROUNDING INSTRUCTIONS:
1. Use the uploaded report as the SOLE source for report-specific values, test results, units, dates, and reference ranges.
2. Use the retrieved MedQuAD context strictly as supporting general medical knowledge.
3. NEVER invent a test result, unit, date, or reference range.
4. NEVER modify or alter any value from the patient's report.
5. NEVER claim or imply that retrieved MedQuAD information came directly from the patient's report.
6. DO NOT diagnose the patient with any disease or medical condition.
7. DO NOT recommend medications, dosages, or medical treatment.
8. If the available information is insufficient or unclear to answer a question, explicitly state so.
9. Explain medical terminology in clear, patient-friendly, simple language.
10. ALWAYS include an educational, non-diagnostic disclaimer emphasizing consultation with a qualified healthcare professional.
"""


def get_llm_api_key() -> Optional[str]:
    """Retrieve LLM API key from environment variables."""
    key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    return key.strip() if key and key.strip() else None


def get_llm_provider_name() -> str:
    """Retrieve configured LLM provider name from environment variables."""
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider:
        return provider
    key = get_llm_api_key()
    if key:
        if os.getenv("GEMINI_API_KEY"):
            return "gemini"
        elif os.getenv("OPENAI_API_KEY"):
            return "openai"
        return "generic"
    return "unconfigured"


def is_llm_configured() -> bool:
    """Check if a valid LLM API key or mock provider configuration is present."""
    provider = get_llm_provider_name()
    if provider == "mock":
        return True
    return get_llm_api_key() is not None


class BaseLLMProvider:
    """Abstract base class for LLM providers."""

    def generate(self, system_instruction: str, user_prompt: str) -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider using HTTP REST."""

    def __init__(self, api_key: str, model_name: Optional[str] = None) -> None:
        self.api_key = api_key
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "gemini-1.5-flash")

    def generate(self, system_instruction: str, user_prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
            f"?key={self.api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data_bytes, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                raise ValueError("Received empty content from Gemini API response.")
        except urllib.error.HTTPError as err:
            raise RuntimeError(f"Gemini API HTTP Error {err.code}: {err.reason}") from err
        except Exception as exc:
            raise RuntimeError(f"Gemini API request failed: {str(exc)}") from exc


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Chat Completions API Provider using HTTP REST."""

    def __init__(self, api_key: str, model_name: Optional[str] = None) -> None:
        self.api_key = api_key
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")

    def generate(self, system_instruction: str, user_prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 800,
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                choices = result.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                raise ValueError("Received empty choice from OpenAI API response.")
        except urllib.error.HTTPError as err:
            raise RuntimeError(f"OpenAI API HTTP Error {err.code}: {err.reason}") from err
        except Exception as exc:
            raise RuntimeError(f"OpenAI API request failed: {str(exc)}") from exc


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider for unit tests."""

    def __init__(
        self,
        mock_response: str = "Mocked patient-friendly educational explanation.",
    ) -> None:
        self.mock_response = mock_response

    def generate(self, system_instruction: str, user_prompt: str) -> str:
        return self.mock_response


def get_llm_provider() -> Optional[BaseLLMProvider]:
    """Factory function to get configured LLM provider instance."""
    name = get_llm_provider_name()
    api_key = get_llm_api_key()

    if name == "mock":
        return MockLLMProvider()
    if not api_key:
        return None

    if name == "openai":
        return OpenAIProvider(api_key=api_key)
    return GeminiProvider(api_key=api_key)


def prepare_prompt(
    report_context: Dict[str, Any],
    retrieved_context: List[Dict[str, Any]],
    user_question: str,
) -> Dict[str, Any]:
    """Format structured prompts clearly separating report facts from retrieved MedQuAD knowledge."""
    params = report_context.get("parameters", [])
    if isinstance(params, list) and params:
        parameters_text = "\n".join(
            f"- Parameter: {p.get('test_name', 'Unknown')}\n"
            f"  Result: {p.get('result_value', 'N/A')} {p.get('unit', '') or ''}\n"
            f"  Reference Range: {p.get('reference_range', 'None')}\n"
            f"  Status: {p.get('status', 'Unknown')}"
            for p in params
        )
    else:
        parameters_text = "No structured lab parameters extracted."

    extracted_text_snippet = report_context.get("extracted_text", "")
    if len(extracted_text_snippet) > 1000:
        extracted_text_snippet = extracted_text_snippet[:1000] + "..."

    if retrieved_context:
        retrieved_text = "\n\n".join(
            f"[Retrieved Record #{i+1} | Source ID: {rec.get('source_row_id')}]\n"
            f"Question: {rec.get('question')}\n"
            f"Answer: {rec.get('answer')}"
            for i, rec in enumerate(retrieved_context)
        )
    else:
        retrieved_text = "No additional medical reference context retrieved."

    meta = report_context.get("report_metadata", {})
    report_date = meta.get("report_date") or "Not specified"

    user_prompt = f"""=== SECTION 1: UPLOADED PATIENT REPORT FACTS ===
Report Date: {report_date}
Extracted Text Snippet:
{extracted_text_snippet}

Structured Lab Results:
{parameters_text}

=== SECTION 2: RETRIEVED MEDICAL REFERENCE KNOWLEDGE (MedQuAD) ===
{retrieved_text}

=== SECTION 3: PATIENT / USER QUESTION ===
{user_question}

=== RESPONSE GUIDELINES ===
- Explain the findings clearly in plain, patient-friendly language.
- Address the user question directly.
- Emphasize that this explanation is for educational purposes only.
"""

    return {
        "system_instruction": SYSTEM_INSTRUCTION,
        "user_prompt": user_prompt,
    }


def generate_response(
    report_context: Dict[str, Any],
    retrieved_context: List[Dict[str, Any]],
    user_question: str,
) -> Dict[str, Any]:
    """Generate grounded LLM explanation or return a clear 'not_configured' state if credentials missing."""
    prompt_dict = prepare_prompt(report_context, retrieved_context, user_question)

    if not is_llm_configured():
        return {
            "status": "not_configured",
            "llm_status": "not_configured",
            "provider": get_llm_provider_name(),
            "answer": (
                "LLM provider is not configured. Configured LLM credentials "
                "(e.g., LLM_API_KEY or GEMINI_API_KEY in .env) are required to generate "
                "automated natural language explanations."
            ),
            "prepared_prompt": prompt_dict,
        }

    provider = get_llm_provider()
    if provider is None:
        return {
            "status": "not_configured",
            "llm_status": "not_configured",
            "provider": get_llm_provider_name(),
            "answer": (
                "LLM provider is not configured. Configured LLM credentials "
                "are required to generate automated natural language explanations."
            ),
            "prepared_prompt": prompt_dict,
        }

    try:
        answer_text = provider.generate(
            system_instruction=prompt_dict["system_instruction"],
            user_prompt=prompt_dict["user_prompt"],
        )
        return {
            "status": "success",
            "llm_status": "configured",
            "provider": get_llm_provider_name(),
            "answer": answer_text,
            "prepared_prompt": prompt_dict,
        }
    except Exception as exc:
        safe_error_msg = str(exc)
        if "key=" in safe_error_msg:
            safe_error_msg = safe_error_msg.split("key=")[0] + "key=[REDACTED]"

        return {
            "status": "error",
            "llm_status": "error",
            "provider": get_llm_provider_name(),
            "answer": (
                "Failed to generate explanation due to an LLM provider error. "
                "Please check your API key configuration and network connectivity."
            ),
            "error": safe_error_msg,
            "prepared_prompt": prompt_dict,
        }
