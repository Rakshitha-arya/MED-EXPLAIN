"""Tests for llm_service abstraction, grounding prompts, and provider error handling."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from services.llm_service import (
    GeminiProvider,
    MockLLMProvider,
    OpenAIProvider,
    generate_response,
    get_llm_provider,
    is_llm_configured,
    prepare_prompt,
)


def test_is_llm_configured_behavior():
    with patch.dict(os.environ, {}, clear=True):
        assert not is_llm_configured()

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-123"}):
        assert is_llm_configured()

    with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}):
        assert is_llm_configured()


def test_get_llm_provider_factory():
    with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}):
        provider = get_llm_provider()
        assert isinstance(provider, MockLLMProvider)

    with patch.dict(os.environ, {"GEMINI_API_KEY": "gemini-key-123"}):
        provider = get_llm_provider()
        assert isinstance(provider, GeminiProvider)

    with patch.dict(os.environ, {"OPENAI_API_KEY": "openai-key-123", "LLM_PROVIDER": "openai"}):
        provider = get_llm_provider()
        assert isinstance(provider, OpenAIProvider)

    with patch.dict(os.environ, {}, clear=True):
        provider = get_llm_provider()
        assert provider is None


def test_generate_response_unconfigured():
    report_context = {
        "report_metadata": {"report_date": "2026-09-18"},
        "extracted_text": "Hemoglobin: 11.0 g/dL",
        "parameters": [
            {
                "test_name": "Hemoglobin",
                "result_value": "11.0",
                "unit": "g/dL",
                "reference_range": "13.5 - 17.5",
                "status": "Low",
            }
        ],
    }
    retrieved_context = [
        {
            "source_row_id": 42,
            "question": "What is anemia?",
            "answer": "Anemia is a condition...",
            "similarity": 0.85,
        }
    ]

    with patch.dict(os.environ, {}, clear=True):
        resp = generate_response(
            report_context, retrieved_context, "What does low hemoglobin mean?"
        )
        assert resp["status"] == "not_configured"
        assert resp["llm_status"] == "not_configured"
        assert "LLM provider is not configured" in resp["answer"]
        assert "prepared_prompt" in resp


def test_generate_response_mock_configured():
    report_context = {
        "report_metadata": {"report_date": "2026-09-18"},
        "extracted_text": "Glucose: 140 mg/dL",
        "parameters": [
            {
                "test_name": "Glucose",
                "result_value": "140",
                "unit": "mg/dL",
                "reference_range": "70 - 99",
                "status": "High",
            }
        ],
    }
    retrieved_context = []

    with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}):
        resp = generate_response(
            report_context, retrieved_context, "Can you explain high glucose?"
        )
        assert resp["status"] == "success"
        assert resp["llm_status"] == "configured"
        assert "Mocked patient-friendly educational explanation" in resp["answer"]


def test_generate_response_provider_failure():
    report_context = {"extracted_text": "Test"}
    retrieved_context = []

    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
        with patch("services.llm_service.GeminiProvider.generate") as mock_gen:
            mock_gen.side_effect = RuntimeError("Network timeout connecting to Gemini API")
            resp = generate_response(report_context, retrieved_context, "Explain test")
            assert resp["status"] == "error"
            assert resp["llm_status"] == "error"
            assert "Failed to generate explanation" in resp["answer"]
            assert "Network timeout" in resp["error"]


def test_prepare_prompt_grounding_structure():
    report_context = {
        "report_metadata": {"report_date": "2026-09-18"},
        "extracted_text": "Sample text",
        "parameters": [
            {
                "test_name": "WBC",
                "result_value": "12.5",
                "unit": "x10^3/uL",
                "reference_range": "4.5 - 11.0",
                "status": "High",
            }
        ],
    }
    retrieved_context = [
        {
            "source_row_id": 101,
            "question": "What causes elevated WBC?",
            "answer": "Leukocytosis occurs...",
            "similarity": 0.88,
        }
    ]

    prompts = prepare_prompt(
        report_context, retrieved_context, "What does elevated WBC mean?"
    )

    system_instruction = prompts["system_instruction"]
    user_prompt = prompts["user_prompt"]

    assert "DO NOT diagnose" in system_instruction
    assert "educational, non-diagnostic disclaimer" in system_instruction.lower()
    assert "UPLOADED PATIENT REPORT FACTS" in user_prompt
    assert "WBC" in user_prompt
    assert "12.5" in user_prompt
    assert "RETRIEVED MEDICAL REFERENCE KNOWLEDGE" in user_prompt
    assert "What causes elevated WBC?" in user_prompt
    assert "PATIENT / USER QUESTION" in user_prompt
