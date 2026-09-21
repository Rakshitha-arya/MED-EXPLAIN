# Presentation content

## Slide 1 — Title

**MedExplain: Educational Medical Report Explanation Using RAG**  
Laboratory report extraction, MedQuAD retrieval, grounded explanation, and multi-report trends.

## Slide 2 — Problem statement

- Laboratory reports contain unfamiliar test names, values, units, and reference ranges.
- People need an understandable view of report content.
- Any solution must avoid diagnosis, treatment advice, and invented clinical values.

## Slide 3 — Objectives

- Extract report fields from synthetic PDF/image reports.
- Show Low/Normal/High/Unknown only when supported by report data.
- Retrieve supporting general medical knowledge.
- Support educational explanation, chat, comparison, and trends.

## Slide 4 — Existing system

- Reports are often read manually and can be difficult for non-specialists.
- Generic information sources are not separated from a specific report.
- Static report viewing does not provide structured comparison across reports.

## Slide 5 — Proposed system

- React + Flask application for local report processing.
- PDF text extraction with OCR fallback for scanned/image reports.
- Structured parameter parsing and MedQuAD-based RAG.
- Optional grounded LLM explanation and multi-report trend view.

## Slide 6 — System architecture

- React JSX frontend communicates with Flask APIs.
- Backend validates upload, extracts text, parses fields, persists reports, retrieves FAISS context, and optionally calls an LLM provider.
- Existing read-only FAISS index and metadata each contain 16,407 records.
- Use the Mermaid diagram in [architecture.md](architecture.md).

## Slide 7 — Technologies used

- Python, Flask, Flask-CORS, pytest
- React, JSX, Vite
- PyMuPDF, Pillow, pytesseract/Tesseract
- Sentence Transformers (`all-MiniLM-L6-v2`), FAISS, MedQuAD

## Slide 8 — Medical report processing

- Validate allowed type, size, and content signature.
- Store with generated UUID filename.
- Extract PDF text or use OCR when available.
- Parse test name, value, unit, range, date, and status.
- Missing range or qualitative result remains Unknown.

## Slide 9 — RAG + FAISS + LLM workflow

- Embed report-aware question with Sentence Transformer.
- FAISS retrieves similar MedQuAD records.
- Prompt separates uploaded report facts from retrieved general knowledge.
- LLM instructions prohibit invented values, diagnoses, and treatment recommendations.

## Slide 10 — Multi-report comparison

- Persist each synthetic report independently.
- Compare shared numerical parameters in date order.
- Preserve each report’s own reference range.
- Plot trend only with compatible units.

## Slide 11 — Evaluation

- Retrieval evaluated against independently labelled MedQuAD metadata IDs using the actual existing FAISS index.
- Extraction evaluated using synthetic reports with expected fields.
- OCR CER/WER not measured because Tesseract was unavailable.

## Slide 12 — Results

| Metric | Result |
| --- | ---: |
| Recall@1 / Precision@1 | 0.6000 / 0.6000 |
| Recall@3 / Precision@3 | 1.0000 / 0.3333 |
| Recall@5 / Precision@5 | 1.0000 / 0.2000 |
| MRR | 0.7667 |
| Extraction precision / recall / F1 | 1.0000 / 1.0000 / 1.0000 |

## Slide 13 — Limitations

- Parser supports common layouts, not every report format.
- OCR requires local Tesseract installation.
- Retrieval is limited to MedQuAD.
- The app is educational, not clinically validated or diagnostic.

## Slide 14 — Future scope

- Broader parser templates and approved synthetic OCR evaluation.
- Accessibility improvements and authenticated encrypted storage for a future production design.
- Additional curated sources and clinical review before real-world use.

## Slide 15 — Conclusion

- MedExplain demonstrates safe report extraction, RAG retrieval, optional grounded generation, comparison, and trend visualisation.
- It preserves report facts, avoids diagnosis and treatment advice, and uses synthetic data for demonstration.
- Educational disclaimer: it does not replace a qualified healthcare professional.
