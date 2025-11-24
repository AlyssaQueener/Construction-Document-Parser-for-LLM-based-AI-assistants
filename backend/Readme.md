# Backend - FastAPI Server

## Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Run
```bash
fastapi dev main.py
```

Server runs on http://localhost:8000

## API Endpoints

- POST `/drawing_parser/` - Parse floor plans
- POST `/gantt_parser/{chart_format}` - Parse Gantt charts
- POST `/financial_parser/` - Parse BOQ documents