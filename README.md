# Construction Document Parser for LLM-based AI assistants

A focused toolkit that converts construction documents (floor plans, Gantt charts, BOQs) into structured, LLM-friendly JSON and provides an AI Q&A layer on top of parsed documents.

## Key features
- Drawing parser: extract title block metadata, rooms (deterministic or AI), and full-plan hybrid extraction
- Gantt parser: extract tasks, dates and dependencies from visual or tabular Gantt charts
- Financial (BOQ) parser: extract tabular cost data and structure it for downstream use
- AI Q&A endpoint: ask natural-language questions about parsed documents
- Simple React frontend for uploads, preview and AI interaction

---

## Quick start (local)
Prereqs: Python 3.9+ and Node.js (recommended 16+)

1. Clone the repo

   git clone <repo-url>
   cd Construction-Document-Parser-for-LLM-based-AI-assistants

2. Backend (FastAPI)

   - Create virtualenv and install dependencies
     python -m venv .venv
     .venv\Scripts\activate    # Windows
     source .venv/bin/activate  # macOS / Linux
     pip install -r requirements.txt

   - Run locally
     uvicorn main:app --reload --port 8000

   The API docs will be available at http://127.0.0.1:8000/docs

3. Frontend (React)

   cd frontend
   npm install
   npm start

   Open http://localhost:3000 and use the UI to upload files and try the parsers.

---

## API (examples)
All file uploads use multipart/form-data and return a standardized JSON response with fields: `input_format`, `is_extraction_succesful`, `confident_value`, `extraction_method`, `result`.

- Parse drawing (title block / rooms / full plan)

  POST /drawing_parser/{content_type}/
  content_type: `titleblock-hybrid`, `rooms-deterministic`, `rooms-ai`, `full-plan-ai`
  Example:
    curl -X POST "http://localhost:8000/drawing_parser/titleblock-hybrid/" -F "file=@floorplan.pdf"

- Parse Gantt chart

  POST /gantt_parser/{chart_format}
  chart_format: `visual`, `tabular`, `full_ai`
  Example:
    curl -X POST "http://localhost:8000/gantt_parser/visual" -F "file=@gantt.pdf"

- Parse Bill of Quantities (BOQ)

  POST /financial_parser/
  Example:
    curl -X POST "http://localhost:8000/financial_parser/" -F "file=@boq.pdf"

- Ask AI about a parsed document

  POST /ask_ai/
  Body (application/json): { "question": "...", "document_data": <parsed-result-object> }

---

## Development notes
- The backend is a FastAPI app exposed in `main.py` and returns a consistent `Response` model (see `main.py`).
- Set OPENAI credentials via env var `OPENAI_API_KEY` when running the backend in production. (Currently the repo contains a hardcoded API key — replace with env var before deploying.)
- Large PDF/image uploads may take several seconds to parse; Gantt/BOQ parsing expects PDFs.

---

## Project structure (high level)
- main.py — FastAPI application and endpoints
- src/ — parser modules (gantt2data, plan2data, boq2data)
- frontend/ — React UI

---

## Contributing
- Open an issue to discuss larger changes before starting work.
- Fork, create a feature branch, add tests where appropriate, then open a PR.

---

## Authors / Contact
- Alyssa, Bahar, Rebekka (see project frontend footer for links)

---

## License
No license file included — add a LICENSE (e.g., MIT) if you intend to open-source this project.

---

If you'd like, I can also:
- Add an example Postman collection or curl scripts for CI tests
- Add a short developer guide for adding new parser modules

