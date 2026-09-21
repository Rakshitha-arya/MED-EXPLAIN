# Stage 8 evaluation results

Evaluation run: 2026-09-18, using the existing read-only 16,407-record FAISS index and five independently labelled MedQuAD metadata records.

| Retrieval metric | Measured result |
| --- | ---: |
| Recall@1 | 0.6000 |
| Precision@1 | 0.6000 |
| Recall@3 | 1.0000 |
| Precision@3 | 0.3333 |
| Recall@5 | 1.0000 |
| Precision@5 | 0.2000 |
| MRR | 0.7667 |

Synthetic report extraction covered 6 parameters and 24 exact field assertions (test name matching plus result, unit, reference range, and qualitative/numeric status): precision 1.0000, recall 1.0000, F1 1.0000, and field accuracy 1.0000.

OCR CER/WER were not measured in this environment because the Tesseract executable is unavailable. OCR unavailability is handled as a documented 422 response; no OCR metric is reported.
