# MedExplain: Educational Medical Report Explanation Platform

## Abstract

MedExplain is a local-first educational web application that accepts synthetic PDF or image laboratory reports, extracts structured report facts, retrieves relevant general medical knowledge from MedQuAD, and optionally produces a grounded explanation. It also compares numerical values across uploaded reports and displays trends. It is explicitly not a diagnostic or treatment system.

## Problem statement

Laboratory reports can contain unfamiliar test names, units, reference ranges, and status labels. People may need a clear way to view what a report contains while keeping report-specific facts separate from general medical information.

## Motivation

The project demonstrates an end-to-end application of document processing, natural-language retrieval, and safe generative-AI integration for educational use. It makes extracted values visible without claiming clinical interpretation or replacing a healthcare professional.

## Objectives

- Accept PDF, JPG, JPEG, and PNG report uploads within the configured size limit.
- Extract report text and structured laboratory fields.
- Preserve the report’s values, units, dates, and reference ranges exactly as extracted.
- Classify numeric results as Low, Normal, High, or Unknown only when the supplied range supports it.
- Retrieve supporting, general MedQuAD knowledge from a read-only FAISS index.
- Provide optional grounded explanations and report-aware chat.
- Compare multiple synthetic reports and display numerical trends.

## Proposed solution and main features

The React frontend sends an upload to a Flask API. The backend validates the file type, size, and content signature; gives it an opaque UUID filename; extracts text from a PDF text layer or attempts OCR for a scanned/image report; parses laboratory lines; persists report metadata and parameters; and retrieves supporting context from MedQuAD. The LLM prompt separates patient-report facts from retrieved reference knowledge and prohibits diagnosis, treatment recommendations, and invented report values or ranges.

Main features include PDF/image ingestion, OCR fallback, field extraction, Low/Normal/High/Unknown labels, MedQuAD RAG retrieval, optional LLM explanation, chatbot interaction, multi-report comparison, and trend visualisation.

## System architecture

The complete architecture is documented in [architecture.md](architecture.md). In short, React + JSX communicates with Flask over HTTP; Flask coordinates validation, extraction, parsing, persistence, retrieval, and optional LLM generation. FAISS and MedQuAD metadata are loaded read-only. Report records are stored locally as runtime JSON files.

## Complete workflow

1. A user uploads a synthetic PDF, JPG, JPEG, or PNG report.
2. The backend validates extension, size, and content structure, then stores the upload under a generated identifier.
3. PyMuPDF extracts PDF text. For image reports or PDFs without useful text, the OCR service uses Tesseract when it is available.
4. The parser extracts report date, test name, result, unit, reference range, numeric value when possible, and status.
5. The report is persisted for later display, chat, comparison, and trend analysis.
6. The RAG service embeds a query, searches the existing MedQuAD FAISS index, and returns general knowledge records with source row IDs.
7. An optional configured LLM receives separated report facts and retrieved knowledge. The mock provider is used in automated tests.
8. A second report can be uploaded; shared numerical parameters can then be compared chronologically and plotted.

## Technology stack

| Area | Actual implementation |
| --- | --- |
| Frontend | React 19, JSX, Vite, CSS |
| Backend | Python, Flask, Flask-CORS |
| PDF processing | PyMuPDF |
| Image handling / OCR bridge | Pillow and pytesseract |
| NLP and retrieval embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector search | FAISS IndexFlatIP with L2-normalized vectors |
| Data source | Local MedQuAD-derived processed data and metadata |
| Optional generation | MockLLMProvider for tests; optional Gemini/OpenAI-compatible HTTP providers |
| Tests | pytest |

## Python, ML, deep learning, and NLP

Python implements the backend services, tests, evaluation utilities, and local persistence. The project uses machine learning for semantic retrieval rather than a trained diagnostic classifier. Its deep-learning component is the pre-trained `all-MiniLM-L6-v2` Sentence Transformer used to convert text into embeddings; MedExplain does not train or fine-tune this model. NLP is used to embed report-aware questions and retrieve semantically related MedQuAD records. Rule-based parsing extracts the report’s visible laboratory fields.

## OCR

OCR supports image reports and scanned PDFs through Tesseract, invoked through pytesseract after image preparation. Text-based PDFs use direct PyMuPDF extraction first. At the verified evaluation environment, the Tesseract executable was unavailable, so OCR CER and WER were not measured; the application returns a clear OCR-unavailable response instead of fabricating text or metrics.

## Sentence Transformers, FAISS, RAG, LLM, and generative AI

Sentence Transformers produce 384-dimensional semantic embeddings. FAISS searches the existing normalized-vector index using inner product, equivalent to cosine similarity for these vectors. The index contains 16,407 vectors and its metadata contains 16,407 records.

Retrieval-augmented generation (RAG) first retrieves general MedQuAD knowledge and then places it in a prompt separately from report facts. The optional LLM is a generative-AI component, not a clinical decision-maker. It is instructed to use the uploaded report as the sole source for report-specific values and ranges, to avoid diagnosis and treatment recommendations, and to include an educational disclaimer. Automated tests use `MockLLMProvider`, never a real API call.

## Medical report analysis and multi-report comparison

The parser recognises common colon-separated and whitespace-delimited laboratory lines. Numeric results are compared only with the report-provided range. Missing ranges and qualitative values remain Unknown. The comparison service preserves each report’s own range and date, avoids numerical change claims for incompatible units, and returns chronological measurements for trend charts.

## Evaluation methodology and actual results

The evaluation uses synthetic reports and independently labelled MedQuAD metadata IDs. Retrieval is measured against results from the actual existing FAISS index; relevance is not inferred from retrieved hits. Extraction checks synthetic fields including name, result, unit, range, and qualitative status. The complete measured results are in [evaluation.md](evaluation.md): Recall@1 0.6000, Precision@1 0.6000, Recall@3 1.0000, Precision@3 0.3333, Recall@5 1.0000, Precision@5 0.2000, and MRR 0.7667. Synthetic extraction precision, recall, F1, and field accuracy were each 1.0000.

## Limitations

- The parser supports common report layouts, not every laboratory format.
- OCR depends on the local Tesseract installation and was unavailable in the verified environment.
- Retrieval is limited to the local MedQuAD corpus and the quality of semantic matches.
- Optional LLM output requires local configuration and is not clinically validated.
- The application stores runtime uploaded synthetic reports locally; it is not a production health-record system.

## Privacy and security

Uploads use generated UUID filenames rather than user filenames for storage. The backend validates extension, content signature, and size; rejects traversal-like report identifiers; avoids exposing filesystem paths in normal responses; and keeps `.env` files and API keys out of version control. The project uses synthetic data only for demonstration and tests. It does not document or include API keys, real patient data, or clinical validation claims.

## Future scope

Possible future work includes broader parser templates, OCR installation guidance and evaluation on approved synthetic image sets, accessibility improvements, authenticated encrypted production storage, audit logging, additional curated knowledge sources, and clinical review before any real-world health deployment. These are future ideas, not current functionality.

## Educational and non-diagnostic disclaimer

MedExplain is for educational and informational purposes only. It is not a diagnostic tool, does not prescribe treatment, and does not replace consultation with a qualified healthcare professional.
