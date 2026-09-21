# MedExplain demonstration checklist

- Start the Flask backend from `backend` and the Vite frontend from `frontend`.
- Open the frontend, confirm the educational disclaimer, and upload a synthetic text-based PDF.
- Confirm the extraction method is `pdf_text`, the report date and structured test fields appear, and statuses are shown without a diagnosis.
- Upload a synthetic scanned PDF or PNG with Tesseract available; otherwise demonstrate the clear OCR-unavailable message.
- Show retrieved MedQuAD records and explain that they are general reference knowledge, not report facts.
- With `LLM_PROVIDER=mock`, ask a chat question and show the report-aware mocked answer and disclaimer. With no LLM configuration, show the non-error `not_configured` response.
- Upload a second synthetic report for the same laboratory test with a different date.
- Open Comparison, choose both reports, inspect the comparison table, and select the parameter trend chart.
- Demonstrate rejected uploads: unsupported extension, content/extension mismatch, oversized file, malformed PDF, and an empty file.
- Demonstrate missing reference range and qualitative result handling: each remains `Unknown` rather than receiving an invented range or clinical interpretation.
- Confirm report IDs are opaque UUID filenames and that no filesystem path or API key is shown in the UI or API response.
