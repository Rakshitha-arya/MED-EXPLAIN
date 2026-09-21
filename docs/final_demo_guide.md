# Final demonstration guide

Use only synthetic reports created for the demonstration. Do not upload real patient data. Throughout the demo, state that MedExplain is educational and non-diagnostic.

## 1. Start the backend

From `backend`, run `..\.venv\Scripts\python.exe app.py`.

Tell the evaluator: “The Flask backend exposes report ingestion, retrieval, chat, comparison, and trend APIs. It loads the existing FAISS index; it does not build an index when the app starts.”

## 2. Start the frontend

From `frontend`, run `npm.cmd run dev`.

Tell the evaluator: “The frontend is implemented with React and JSX and calls the Flask API over HTTP.”

## 3. Open the frontend

Open the local Vite address shown in the terminal, normally `http://localhost:5173`.

Tell the evaluator: “The interface displays an educational disclaimer before any report analysis.”

## 4. Upload the first synthetic report

Use a synthetic text PDF containing, for example, a date and fields such as `Hemoglobin: 10.2 g/dL (12-16)` and `HBsAg: Positive (Negative)`. Upload it through the home page.

Tell the evaluator: “The upload is limited to PDF/JPG/JPEG/PNG, checked for size and matching content, and saved under an opaque UUID rather than its original filename.”

## 5. Show extracted information

On the analysis page, show the extraction method, report date, and extracted text snippet.

Tell the evaluator: “Text PDFs are read directly with PyMuPDF. Scanned PDFs and images use OCR only when Tesseract is available.”

## 6. Show structured test parameters

Show the parameter table.

Tell the evaluator: “The parser extracts the test name, result value, unit, reference range, and status from the report text. It does not generate missing report values.”

## 7. Explain values, units, and ranges

Point to the hemoglobin value, its `g/dL` unit, and its `12-16` reference range.

Tell the evaluator: “These are report facts. The application preserves them rather than substituting a general range.”

## 8. Explain status labels

Show Low, Normal, High, and Unknown where represented by the synthetic report. A missing range or qualitative value such as `Positive (Negative)` stays Unknown.

Tell the evaluator: “A numeric value is labelled only when its supplied range permits comparison. Unknown prevents an invented interpretation.”

## 9. Generate an AI explanation

For a fully local demo, set `LLM_PROVIDER=mock` in an untracked local `backend/.env` before starting the backend, then use the explanation button. If it is not configured, demonstrate the clear `not_configured` response instead.

Tell the evaluator: “The LLM prompt separates report facts from general retrieved knowledge, prohibits diagnosis and treatment recommendations, and requires an educational disclaimer. Automated tests use the mock provider, not a real API.”

## 10. Ask a chatbot question

Ask a question such as “What does this result mean?” through the report chatbot.

Tell the evaluator: “The chat endpoint is report-aware: it passes the existing extracted report context and retrieves supporting general knowledge.”

## 11. Show RAG grounding and sources

Show the retrieved MedQuAD cards, including question, answer, source row ID, and similarity score.

Tell the evaluator: “These cards are general MedQuAD knowledge, not content from the uploaded report. The FAISS index has 16,407 vectors and 16,407 metadata records.”

## 12. Upload a second synthetic report

Upload another synthetic PDF for the same parameter on a later date, for example `Hemoglobin: 11.5 g/dL (12-16)`.

Tell the evaluator: “Each uploaded report is kept as a separate local record with its own extracted range and date.”

## 13. Compare reports

Open the Comparison tab, select the two reports, and run comparison.

Tell the evaluator: “Comparison is based only on persisted extracted values. It does not diagnose a cause for change.”

## 14. Show numerical changes and trend chart

Select the shared parameter and show its chronological measurements and chart.

Tell the evaluator: “The service calculates a numerical change only when units are compatible. It retains each report’s own reference range.”

## 15. Close with the disclaimer

Point out the disclaimer visible in the interface.

Tell the evaluator: “This project is an educational document-processing and retrieval demonstration. It is not clinically validated, does not diagnose conditions, and does not recommend treatments.”
