# AI Coach API — Phase 1

This is the Phase 1 FastAPI and PostgreSQL foundation for AI Coach: IELTS learning records, writing submissions, and university/programme requirements.

## Prerequisites

- Python 3.11 or newer
- PostgreSQL running locally

Create the database once:

```sql
CREATE DATABASE ai_coach;
```

## Run locally

From this `backend` directory, create and activate a virtual environment, then install the requirements:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your PostgreSQL password and a real `SECRET_KEY`, then start the API:

```powershell
uvicorn app.main:app --reload
```

Check `http://127.0.0.1:8000/health` and browse the generated API docs at `http://127.0.0.1:8000/docs`.

Open the student dashboard at `http://127.0.0.1:8000/app/`.

`app/main.py` creates the initial tables on startup. Use Alembic migrations before deploying to a shared or production database.

## Included MVP features

- JWT registration and login
- Student academic profile and PDF transcript text extraction
- IELTS lessons, practice-attempt storage, manual band score calculation, and writing feedback
- Speaking transcript feedback and IELTS coach tips (replace deterministic feedback with a configured LLM for production)
- Rule-based university eligibility and match ranking using stored requirements
- A browser dashboard with sample lessons and clearly marked demonstration university data
