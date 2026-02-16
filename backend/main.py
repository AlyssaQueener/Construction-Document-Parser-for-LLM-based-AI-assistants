from fastapi.middleware.cors import CORSMiddleware
import gc
from fastapi import FastAPI, UploadFile, HTTPException
from PIL import Image 
import src.plan2data.titleBlockInfo as floorplan_parser
import io
import uuid
import src.gantt2data.ganttParser as gantt_parser
import src.boq2data.camelot_setup.boq2data_gemini as boq
import src.plan2data.voronoi_functions as vor
import src.plan2data.full_plan_ai as full
import src.plan2data.helper as helper
from pydantic import BaseModel
from enum import Enum
from openai import OpenAI
import json
from fastapi import Request


# ========================================
# run fastapi dev main.py -> Documentation at http://127.0.0.1:8000/docs
# ========================================

# ========================================
# OPENAI API KEY
# ========================================
import os
os.environ['OMP_NUM_THREADS'] = '1'  # Limit OpenCV threads
os.environ['OPENBLAS_NUM_THREADS'] = '1' 
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)


class Response(BaseModel):
    input_format: str
    is_extraction_succesful: bool
    confident_value: float | None
    extraction_method: str
    result: str | dict | list 

class ContentType(str, Enum):
    titleblock = "titleblock-hybrid"
    plan_deterministic = "rooms-deterministic"
    plan_ai= "rooms-ai"
    full_result = "full-plan-ai"

class ChartFormat(str, Enum):
    visual = "visual"
    tabular = "tabular"
    full_ai= "full ai"


# ========================================
# TAG METADATA (sidebar grouping in /docs)
# ========================================

tags_metadata = [
    {
        "name": "Health",
        "description": "Server status and health checks.",
    },
    {
        "name": "Program Parser",
        "description": (
            "Upload a **Gantt chart PDF** and receive structured JSON with tasks, durations, "
            "dependencies, and milestones.\n\n"
            "**Parsing strategies:**\n\n"
            "| Strategy | Best For |\n"
            "|----------|----------|\n"
            "| `visual` | Image-heavy charts — uses computer-vision bar detection + OCR |\n"
            "| `tabular` | Charts with clear table grids — uses Camelot table extraction |\n"
            "| `full ai` | Non-standard layouts — end-to-end multimodal LLM extraction |"
        ),
    },
    {
        "name": "Financial Parser",
        "description": (
            "Upload a **Bill of Quantities (BoQ) PDF** and receive structured JSON with "
            "line items, quantities, units, unit prices, and totals. "
            "Uses AI-assisted extraction with Mistral."
        ),
    },
    {
        "name": "Drawing Parser",
        "description": (
            "Upload **architectural floor plans** (PDF or image) and extract structured data.\n\n"
            "| Mode | Input | Description |\n"
            "|------|-------|-------------|\n"
            "| `titleblock-hybrid` | PDF / Image | Title-block metadata (project name, date, scale, etc.) via hybrid OCR + AI |\n"
            "| `rooms-deterministic` | PDF | Room detection and adjacency via Voronoi tessellation (fast, no AI) |\n"
            "| `rooms-ai` | PDF / Image | AI-based room detection with neighbouring-room analysis |\n"
            "| `full-plan-ai` | PDF | Full extraction combining Voronoi geometry with AI post-processing |"
        ),
    },
    {
        "name": "AI Chatbot",
        "description": (
            "Ask natural-language questions about previously parsed document data. "
            "Send the parsed JSON together with your question and receive an AI-generated answer "
            "(powered by GPT-4o-mini)."
        ),
    },
]


description = """
## Overview

**ConDoc Parser** converts construction documents into structured JSON, 
ready for downstream applications and LLM-based AI assistants.

**Workflow:** Upload a file → choose a parsing strategy → receive clean, structured data.

### Supported Document Types

| Category | Documents | Accepted Formats |
|----------|-----------|------------------|
| **Financial** | Bill of Quantities (BoQ) | PDF |
| **Program** | Gantt Charts | PDF |
| **Drawings** | Architectural Floor Plans | PDF, JPEG, PNG |

### Quick Start

1. Pick the parser endpoint for your document type.
2. `POST` your file as `multipart/form-data`.
3. Receive a JSON response with extracted data, extraction method, and confidence score.
4. *(Optional)* Send the parsed result to `/ask_ai/` with a question for AI-powered insights.

---

*Developed as part of the ITBE Master's programme at TU München.*
"""



app = FastAPI(
    title="ConDoc Parser — Construction Document Parser API",
    description=description,
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "ConDoc Parser Team",
        "url": "https://construction-doc-parser.onrender.com",
    },
    license_info={
        "name": "MIT",
    },
)


## after installation of fastapi run -- fastapi dev main.py -- in terminal to start server locally 
## go to http://127.0.0.1:8000/docs to view the automatically created api docs

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://construction-doc-parser.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Returns basic server info. Use this to verify the API is running.",
)
async def hello_world():
    return {"This is": "Document Parser for LLM based AI assistants",
            "To try out API" : "Go to -> /docs"
            }
########################################## GANT##########################################    
@app.post(
    "/gantt_parser/{chart_format}",
    tags=["Program Parser"],
    response_model=Response,
    summary="Parse a Gantt chart PDF",
    description=(
        "Upload a Gantt chart in **PDF format** and select a parsing strategy.\n\n"
        "**Strategies:**\n\n"
        "- `visual` — Vision-based bar detection + OCR. Best for image-rendered charts.\n"
        "- `tabular` — Table extraction via Camelot. Best for charts with clear grid structure.\n"
        "- `full ai` — Multimodal LLM extraction. Most flexible, handles non-standard layouts.\n\n"
        "Returns extracted tasks with names, start/end dates, durations, and dependencies."
    ),
    responses={
        200: {
            "description": "Successfully parsed Gantt chart.",
            "content": {
                "application/json": {
                    "example": {
                        "input_format": "application/pdf",
                        "is_extraction_succesful": True,
                        "confident_value": None,
                        "extraction_method": "visual",
                        "result": [
                            {"task": "Foundation Work", "start": "2024-01-15", "end": "2024-03-01", "duration_days": 46}
                        ],
                    }
                }
            },
        },
        400: {"description": "Invalid file type — only PDF is accepted."},
        500: {"description": "Internal processing error."},
    },
)
async def create_upload_file_gantt(file: UploadFile, chart_format: ChartFormat):
    upload_dir = "uploads"  # Make sure this directory exists
    os.makedirs(upload_dir, exist_ok=True)
    file_path = None
    
    try:
        if not (file.content_type == 'application/pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        file_content = await file.read()
        
        if file.content_type == 'application/pdf':
            with open(file_path, 'wb') as f:
                f.write(file_content)
        else:
            with Image.open(io.BytesIO(file_content)) as im:
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
                im.save(file_path, 'JPEG')
        
        result, method, is_succesful = gantt_parser.parse_gantt_chart(file_path,chart_format)

        response = Response(
            input_format=file.content_type,  
            is_extraction_succesful= is_succesful,
            confident_value=None,
            extraction_method=method,
            result=result
        )
        
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            gc.collect()


    
################################################ FINANCIAL ##########################################################################
@app.post(
    "/financial_parser/",
    tags=["Financial Parser"],
    response_model=Response,
    summary="Parse a Bill of Quantities PDF",
    description=(
        "Upload a **Bill of Quantities (BoQ)** document in PDF format.\n\n"
        "Uses AI-assisted table extraction (Mistral) to identify line items, "
        "quantities, units, unit prices, and totals.\n\n"
        "Returns structured JSON suitable for cost analysis, LLM querying, "
        "or integration into project-management tools."
    ),
    responses={
        200: {
            "description": "Successfully parsed BoQ.",
            "content": {
                "application/json": {
                    "example": {
                        "input_format": "application/pdf",
                        "is_extraction_succesful": True,
                        "confident_value": None,
                        "extraction_method": "mistral-ai",
                        "result": [
                            {"item_no": "3.1", "description": "Reinforced concrete C30/37", "quantity": 120.0, "unit": "m³", "unit_price": 185.00, "total": 22200.00}
                        ],
                    }
                }
            },
        },
        400: {"description": "Invalid file type — only PDF or image accepted."},
        500: {"description": "Internal processing error."},
    },
)
async def create_upload_file_fin(file: UploadFile):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = None
    try:
        if not (file.content_type == 'application/pdf' or file.content_type.startswith('image/')): # type: ignore
            raise HTTPException(status_code=400, detail="File must be a PDF or image")
        
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        file_content = await file.read()
        
        if file.content_type == 'application/pdf':
            with open(file_path, 'wb') as f:
                f.write(file_content)

        #result, method, is_succesful = boq.financial_boq(file_path)
        result, method, is_succesful = boq. extract_boq_mistral(file_path)
        response = Response(
            input_format=file.content_type,  
            is_extraction_succesful= is_succesful,
            confident_value=None,
            extraction_method=method,
            result=result
        )
        
        
        return response
        
       
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            gc.collect()



################################################################## DRAWING ######################################################

@app.post(
    "/drawing_parser/{content_type}/",
    tags=["Drawing Parser"],
    response_model=Response,
    summary="Parse an architectural floor plan",
    description=(
        "Upload an architectural floor plan and choose an extraction mode.\n\n"
        "### Extraction Modes\n\n"
        "| Mode | Accepted Input | What It Extracts |\n"
        "|------|---------------|------------------|\n"
        "| `titleblock-hybrid` | PDF or Image | Title-block metadata: project name, drawing number, date, scale, revision, architect. Hybrid OCR + AI. |\n"
        "| `rooms-deterministic` | PDF only | Room polygons and spatial adjacency via Voronoi tessellation. Fast, fully deterministic. |\n"
        "| `rooms-ai` | PDF or Image | AI-based room detection with neighbouring-room relationships. |\n"
        "| `full-plan-ai` | PDF only | Complete floor-plan extraction: rooms, adjacency, and metadata. Combines Voronoi geometry with AI post-processing. |\n\n"
        "### Tips\n\n"
        "- For `rooms-deterministic` and `full-plan-ai`, upload clean PDF drawings (not scans) for best results.\n"
        "- `titleblock-hybrid` accepts either a PDF (first page is converted) or a direct image of the title block.\n"
        "- `rooms-ai` is the most flexible but may be slower due to LLM inference."
    ),
    responses={
        200: {
            "description": "Successfully parsed floor plan.",
            "content": {
                "application/json": {
                    "examples": {
                        "titleblock": {
                            "summary": "Title-block extraction",
                            "value": {
                                "input_format": "application/pdf",
                                "is_extraction_succesful": True,
                                "confident_value": 0.92,
                                "extraction_method": "hybrid",
                                "result": {
                                    "project_name": "Residential Complex B",
                                    "drawing_number": "A-101",
                                    "date": "2024-06-20",
                                    "scale": "1:100",
                                    "architect": "Studio XY",
                                },
                            },
                        },
                        "rooms_deterministic": {
                            "summary": "Room adjacency (deterministic)",
                            "value": {
                                "input_format": "application/pdf",
                                "is_extraction_succesful": True,
                                "confident_value": None,
                                "extraction_method": "deterministic",
                                "result": {
                                    "rooms": [
                                        {"id": "R1", "label": "Living Room", "area_m2": 28.5},
                                        {"id": "R2", "label": "Kitchen", "area_m2": 12.0},
                                    ],
                                    "adjacencies": [["R1", "R2"]],
                                },
                            },
                        },
                    }
                }
            },
        },
        400: {"description": "Invalid file type for the selected content type."},
        500: {"description": "Internal processing error."},
    },
)
async def create_upload_file_floorplans(file: UploadFile, content_type: ContentType):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = None
    converted_image_path = None  # Track converted image separately
    
    try:
        # Validate file type based on content_type
        if content_type in ["rooms-deterministic", "full-plan-ai"]:
            if not file.content_type == 'application/pdf':
                raise HTTPException(status_code=400, detail="Deterministic or Hybrid plan parsing requires PDF file")
        elif content_type == "titleblock-hybrid":
            # Hybrid accepts both Image and PDF
            if not (file.content_type.startswith('image/') or file.content_type == 'application/pdf'):
                raise HTTPException(status_code=400, detail="Titleblock Hybrid parsing requires Image or PDF file")
        elif content_type =="rooms-ai":
            if not (file.content_type.startswith('image/') or file.content_type == 'application/pdf'):
                raise HTTPException(status_code=400, detail="File must be an image or PDF")
        else:
            if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
        
        # Determine file extension
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Read file content
        file_content = await file.read()
        
        # Save file based on type and content_type
        if file.content_type == 'application/pdf':
            if content_type == "titleblock-hybrid":
                # For titleblock-hybrid: Convert PDF to image
                # First save the PDF temporarily
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                
                # Convert PDF to image (first page only)
                converted_image_paths = helper.convert_pdf2img(file_path, pages=(0,))

                # Extract the first image path from the list
                if isinstance(converted_image_paths, list) and len(converted_image_paths) > 0:
                    converted_image_path = converted_image_paths[0]  # Get first element
                else:
                    converted_image_path = converted_image_paths

                # Use the converted image for processing
                processing_file_path = converted_image_path
            else:
                # For other content types: Save PDF directly
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                processing_file_path = file_path
        else:
            # Process and save image as JPEG
            with Image.open(io.BytesIO(file_content)) as im:
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
                im.save(file_path, 'JPEG')
            processing_file_path = file_path
        
        method = "None"
        is_succesful = False
        confidence = None
        
        # Process based on content_type
        if content_type == "titleblock-hybrid":
            result, method, is_succesful, confidence = floorplan_parser.get_title_block_info(processing_file_path)
            
        elif content_type == "rooms-deterministic":
            result = vor.neighboring_rooms_voronoi(processing_file_path)
            method = "deterministic"
            is_succesful = True
            confidence = None
            
        elif content_type == "rooms-ai":
            result, method, is_succesful, confidence = full.get_neighbouring_rooms_with_ai(processing_file_path)
            
        elif content_type == "full-plan-ai":
            result = vor.extract_full_floorplan(processing_file_path)
            method = "hybrid"
            is_succesful = True
            confidence = None
            
            
        # Create response
        response = Response(
            input_format=file.content_type,  
            is_extraction_succesful=is_succesful,
            confident_value=confidence,
            extraction_method=method,
            result=result
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Cleanup: remove both original and converted files
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        if converted_image_path and os.path.exists(converted_image_path):
            os.remove(converted_image_path)
        gc.collect()
    

# ========================================
# AI CHATBOT
# ========================================
@app.post(
    "/ask_ai/",
    tags=["AI Chatbot"],
    summary="Ask a question about parsed document data",
    description=(
        "Send previously parsed construction-document JSON together with a "
        "natural-language question. The endpoint forwards both to **GPT-4o-mini**, "
        "which answers strictly based on the provided data.\n\n"
        "### Workflow\n\n"
        "1. Parse a document with one of the parser endpoints.\n"
        "2. Take the `result` field from the parser response.\n"
        "3. Send it here as `document_data` along with your `question`.\n\n"
        "### Request Body\n\n"
        "```json\n"
        "{\n"
        '  "question": "What is the most expensive line item?",\n'
        '  "document_data": { "...parsed data..." }\n'
        "}\n"
        "```"
    ),
    responses={
        200: {
            "description": "AI-generated answer.",
            "content": {
                "application/json": {
                    "example": {
                        "answer": "The most expensive line item is 3.1 Reinforced concrete at €22,200.",
                        "model": "gpt-4o-mini",
                        "usage": {"prompt_tokens": 320, "completion_tokens": 45, "total_tokens": 365},
                    }
                }
            },
        },
        400: {"description": "Missing `question` or `document_data` field."},
        500: {"description": "LLM inference error."},
    },
)
async def ask_ai(request: Request):
    """Ask AI questions about parsed construction document data"""
    try:
        data = await request.json()
        question = data.get("question")
        document_data = data.get("document_data")
        
        if not question:
            raise HTTPException(status_code=400, detail="Missing 'question' field")
        
        if not document_data:
            raise HTTPException(status_code=400, detail="Missing 'document_data' field")
        
        prompt = f"""You are a helpful assistant analyzing construction document data.

Here is the parsed construction document data in JSON format:
{json.dumps(document_data, indent=2)}

User question: {question}

Instructions:
- Answer the question based ONLY on the data provided above
- Be concise and specific
- If the information is not in the data, say "This information is not available in the parsed document"
- Focus on construction-related insights

Answer:"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
        return {
            "answer": answer,
            "model": "gpt-4o-mini",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
    except Exception as e:
        print(f"Error in ask_ai: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        gc.collect()
    




# #https://fastapi.tiangolo.com/async/#in-a-hurry maybe have a look at this to improve performance