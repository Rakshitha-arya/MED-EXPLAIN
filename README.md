# MedExplain

MedExplain is an educational, local-first web application for extracting laboratory report fields, showing non-diagnostic status comparisons, retrieving supporting MedQuAD knowledge, and optionally producing grounded explanations. It is not a diagnosis or treatment tool.

## Run locally

```powershell
cd backend
..\.venv\Scripts\python.exe app.py
```

In another terminal:

```powershell
cd frontend
npm run dev
```

Copy `backend/.env.example` to `backend/.env` only when local configuration is needed. Never commit `.env` or API keys. The default frontend API target is `http://localhost:5000`; set `VITE_API_BASE_URL` to override it.

## Verification

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe scripts/run_evaluation.py
..\.venv\Scripts\python.exe scripts/verify_stage8.py
cd ..\frontend
npm run build
```

The FAISS index and its metadata contain 16,407 records. They are loaded read-only; do not run the index builder for normal application use or Stage 8 evaluation.

See [architecture documentation](docs/architecture.md), [actual evaluation results](docs/evaluation.md), and the [demo checklist](docs/demo_checklist.md).
