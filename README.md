# Construction Document Parser for LLM-based AI Assistants

> Turn construction documents — floor plans, Gantt charts, Bills of Quantities — into structured, LLM-friendly JSON, then ask questions about them with a built-in AI assistant.

## The Problem

Construction projects generate vast amounts of digital information — architectural drawings, schedules, contracts, cost breakdowns — yet file structures are typically defined individually by each project participant. The result: inconsistent naming conventions, unstructured folder hierarchies, and heterogeneous data repositories where information is easy to create but hard to find. According to Autodesk (2018), construction professionals spend an average of **5.5 hours per week** just searching for project information. Unification attempts like corporate folder templates are often applied only partially and break down as projects evolve, leading to information loss, version confusion, and costly retrieval errors.

## What This Project Does

This toolkit addresses the retrieval and structuring side of that problem. It takes the document types that construction teams work with daily — floor plans, Gantt charts, Bills of Quantities — and converts them into structured, queryable JSON using a combination of deterministic extraction, OCR, and LLM-based parsing. A built-in AI Q&A layer then lets users ask natural-language questions about the parsed data, removing the need to manually dig through files.

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐     ┌────────────┐
│  PDF / Image │ ──▶ │  Parser Module  │ ──▶ │  Structured  │ ──▶ │  AI Q&A /  │
│  (upload)    │     │  (OCR + AI)     │     │  JSON        │     │  Chat UI   │
└──────────────┘     └─────────────────┘     └──────────────┘     └────────────┘
```
## Live Demo

**API Docs** https://construction-document-parser.onrender.com/docs
**Web app:** https://construction-doc-parser.onrender.com


## Tech Stack

**Backend:** Python 3.9+, FastAPI, Mistral AI, OpenAI API, Tesseract OCR, pdf2image, Pillow  
**Frontend:** React, Node.js 16+  
**Deployment:** Docker-ready, tested on Render (free tier)

## Key Features

**Drawing Parser** — Extract title block metadata, room information (deterministic or AI-driven), and full-plan hybrid extraction from architectural floor plans.

**Gantt Parser** — Parse tasks, dates, and dependencies from visual or tabular Gantt charts. Three strategies: rule-based tabular extraction, hybrid visual parsing, and full AI-driven extraction with Mistral AI fallback.

**Financial (BOQ) Parser** — Extract and structure tabular cost data from Bills of Quantities for downstream analysis.

**AI Q&A** — Ask natural-language questions about any parsed document through the REST API or the integrated chat interface.

**Validation Module** — LLM-as-a-judge validation prompts and test data for evaluating each parser's output quality independently.

## Quick Start (Local)

### Prerequisites

- Python 3.9+
- Node.js 16+
- Tesseract OCR installed and on your `PATH`

### 1. Clone the repo

```bash
git clone <repo-url>
cd Construction-Document-Parser-for-LLM-based-AI-assistants
```

### 2. Backend (FastAPI)

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 3. Frontend (React)

```bash
cd frontend
npm install
npm start
```

Open [http://localhost:3000](http://localhost:3000) to upload files and interact with the parsers.

## API Reference

All file uploads use `multipart/form-data`. Every endpoint returns a standardized JSON response:

```json
{
  "input_format": "pdf",
  "is_extraction_successful": true,
  "confidence_value": 0.92,
  "extraction_method": "hybrid",
  "result": { ... }
}
```

### Drawing Parser

```
POST /drawing_parser/{content_type}/
```

| `content_type` | Description |
|---|---|
| `titleblock-hybrid` | Extract title block metadata using OCR + AI |
| `rooms-deterministic` | Rule-based room extraction |
| `rooms-ai` | AI-driven room extraction |
| `full-plan-ai` | Full architectural plan analysis |

```bash
curl -X POST "http://localhost:8000/drawing_parser/titleblock-hybrid/" \
  -F "file=@floorplan.pdf"
```

### Gantt Parser

```
POST /gantt_parser/{chart_format}
```

| `chart_format` | Description |
|---|---|
| `visual` | Image-based Gantt chart parsing |
| `tabular` | Table-based Gantt chart parsing |
| `full_ai` | End-to-end AI extraction |

```bash
curl -X POST "http://localhost:8000/gantt_parser/visual" \
  -F "file=@gantt.pdf"
```

### Financial (BOQ) Parser

```bash
curl -X POST "http://localhost:8000/financial_parser/" \
  -F "file=@boq.pdf"
```

### AI Q&A

```bash
curl -X POST "http://localhost:8000/ask_ai/" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the total project duration?",
    "document_data": { ... }
  }'
```

## Validation

The validation module provides LLM-as-a-judge prompts and reference test data for evaluating parser output quality. Each parser has its own validation set so you can benchmark accuracy independently.

See `src/validation/` for prompt templates and test fixtures.

## Project Structure

```
├── main.py                  # FastAPI app, route definitions, Response model
├── requirements.txt
├── src/
│   ├── plan2data/           # Drawing / floor plan parser modules
│   ├── gantt2data/          # Gantt chart parser modules
│   ├── boq2data/            # Bill of Quantities parser modules
│   └── validation/          # LLM-as-a-judge prompts and test data
├── frontend/
│   ├── src/                 # React components, chat UI
│   └── public/
└── README.md
```

## Development Notes

- Large PDF/image uploads may take several seconds; parsing is CPU- and API-bound.
- Gantt and BOQ parsers expect PDF input. The drawing parser also accepts common image formats.
- When OCR confidence is low, the system falls back to AI-based extraction automatically.

## Deployment

The project has been tested on Render's free tier. Note that free-tier instances spin down after inactivity, so expect cold-start delays of ~30–50 seconds on the first request. The React frontend includes a loading state to handle this gracefully.

For Docker-based deployment, see the `Dockerfile` in dockerization branch


## Authors

Alyssa, Bahar, Rebekka — see the application footer for contact links.

## License

No license file is currently included. If you intend to open-source this project, consider adding an [MIT](https://choosealicense.com/licenses/mit/) or [Apache 2.0](https://choosealicense.com/licenses/apache-2.0/) license.