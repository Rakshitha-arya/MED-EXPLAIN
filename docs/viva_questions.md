# Viva questions and concise answers

1. **What is MedExplain?** An educational web application that extracts laboratory report fields, retrieves general MedQuAD knowledge, and can show grounded explanations.
2. **Why did you build this project?** Laboratory reports can be hard to read because they contain unfamiliar names, units, and ranges.
3. **What problem does it solve?** It organizes report information and presents supporting general knowledge without claiming diagnosis.
4. **What are the main objectives?** Extract report facts, show safe status labels, retrieve knowledge, support educational chat, and compare synthetic reports.
5. **Why is it not a diagnostic system?** It does not determine diseases, prescribe treatment, or claim clinical validation.
6. **What is RAG?** Retrieval-augmented generation retrieves relevant reference information before preparing an LLM prompt.
7. **Why use RAG here?** It gives the explanation general medical context while keeping that context separate from report facts.
8. **What is FAISS?** FAISS is a library for fast similarity search over vectors.
9. **Why use FAISS?** It efficiently searches the local MedQuAD embeddings.
10. **How many records are indexed?** The existing FAISS index and metadata each contain 16,407 records.
11. **What are embeddings?** Numeric vectors that represent the semantic meaning of text.
12. **Why use Sentence Transformers?** They create useful semantic embeddings for questions and medical reference text.
13. **Which embedding model is used?** `sentence-transformers/all-MiniLM-L6-v2`.
14. **Is the transformer trained in this project?** No. The project uses a pre-trained model and does not fine-tune it.
15. **What is NLP?** Natural language processing is the use of computing to work with human language.
16. **How is NLP used here?** It creates semantic query embeddings for retrieval; report parsing is rule based.
17. **What is OCR?** Optical character recognition converts text in an image into machine-readable text.
18. **Why is OCR needed?** Scanned PDFs and image reports may not have a selectable text layer.
19. **How does a text PDF differ from a scanned PDF?** A text PDF has an embedded text layer; a scanned PDF is usually an image and may need OCR.
20. **Which OCR tool is used?** Tesseract through pytesseract, when the executable is installed.
21. **Was OCR evaluated in this environment?** No. Tesseract was unavailable, so CER and WER were not measured.
22. **How does report parsing work?** Regular-expression patterns identify common laboratory lines and extract name, result, unit, and range.
23. **What is a reference range?** A range printed by the report laboratory for a specific test result.
24. **Why preserve the report’s own reference range?** Ranges can differ by laboratory, method, and context, so the app must not invent one.
25. **What do Low, Normal, High, and Unknown mean here?** They are rule-based labels from the supplied numeric value and range; Unknown is used when safe comparison is not possible.
26. **How are qualitative results handled?** They remain Unknown rather than being forced into a numeric label.
27. **What is an LLM?** A large language model generates natural-language text from a prompt.
28. **What is generative AI in this project?** The optional LLM explanation and chat response component.
29. **How is the LLM grounded?** Its prompt separates report facts from retrieved MedQuAD context and gives strict safety instructions.
30. **How is hallucination reduced?** The prompt prohibits invented report values/ranges and limits report facts to the uploaded report.
31. **Can the LLM diagnose a patient?** No. The prompt explicitly forbids diagnosis.
32. **Can it recommend treatment or medication?** No. The prompt explicitly forbids treatment recommendations and dosages.
33. **What is MedQuAD?** A medical question-answer dataset used here as general reference knowledge.
34. **Why MedQuAD?** It provides local medical question-answer content for retrieval demonstrations.
35. **How does retrieval work?** The query is embedded, FAISS returns similar vectors, and the app returns matching MedQuAD records with source IDs.
36. **What is Recall@K?** The fraction of queries for which a relevant record appears in the first K results.
37. **What is Precision@K?** The share of the first K returned results that are relevant.
38. **What is MRR?** Mean reciprocal rank measures how early the first relevant result appears on average.
39. **What are CER and WER?** Character Error Rate and Word Error Rate compare OCR output with known reference text.
40. **What are precision, recall, and F1 for extraction?** They measure correct extraction, completeness, and their balance.
41. **Why use synthetic reports?** They avoid real patient data and allow known expected fields for repeatable tests.
42. **What were the retrieval results?** Recall@1 and Precision@1 were 0.6000; Recall@3 and Recall@5 were 1.0000; MRR was 0.7667.
43. **What were the extraction results?** Synthetic extraction precision, recall, F1, and field accuracy were 1.0000.
44. **How does multi-report comparison work?** It compares saved numerical parameters across report dates.
45. **What is trend analysis here?** It orders compatible numerical measurements by date and shows changes in a chart.
46. **Why check units before a trend calculation?** A numerical change is unsafe or meaningless when units are incompatible.
47. **Why React and JSX?** They support a component-based interactive frontend.
48. **Why Flask?** Flask provides a small Python API layer for the application services.
49. **How do frontend and backend communicate?** The frontend sends multipart uploads and JSON API requests over HTTP.
50. **What security controls are present?** Upload type/size/signature checks, UUID storage names, traversal protection, safe error messages, and ignored `.env` files.
51. **How is privacy handled in the project?** Tests and demos use synthetic data only; no API keys or real patient reports are documented.
52. **What are major limitations?** Parsing layouts vary, OCR needs Tesseract, retrieval is limited to MedQuAD, and the app is not clinically validated.
53. **What is future scope?** More parser templates, approved synthetic OCR evaluation, accessibility, secure production storage, and clinical review.
54. **Why must the disclaimer remain visible?** It clearly states the system is educational and does not replace a qualified healthcare professional.
