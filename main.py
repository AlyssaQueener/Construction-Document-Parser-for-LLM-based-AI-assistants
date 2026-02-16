from fastapi.middleware.cors import CORSMiddleware
import gc 
from fastapi import FastAPI, UploadFile, HTTPException
from PIL import Image 
import src.plan2data.titleBlockInfo as floorplan_parser
import io
import uuid
import src.gantt2data.ganttParser as gantt_parser
import src.boq2data.camelot_setup.boq2data_mistral as boq
import src.plan2data.voronoi_functions as vor
import src.plan2data.full_plan_ai as full
import src.plan2data.helper as helper
from pydantic import BaseModel
from enum import Enum
from openai import OpenAI
import json
from fastapi import Request

import os
os.environ['OMP_NUM_THREADS'] = '1'  # Limit OpenCV threads
os.environ['OPENBLAS_NUM_THREADS'] = '1'

# ========================================
# run fastapi dev main.py -> server   Server started at http://127.0.0.1:8000 
# ========================================

# ========================================
# OPENAI API KEY
# ========================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
# =============================================================================
# IMPORTS AND MODEL DEFINITIONS
# =============================================================================

class Response(BaseModel):
    """
    Standardized response model for all API endpoints.
    
    Provides consistent structure across all parser types (financial, gantt, drawing)
    to enable predictable client-side handling and error management.
    
    Attributes:
        input_format (str): MIME type of uploaded file (e.g., 'application/pdf', 'image/jpeg')
                           Used for validation and logging
        
        is_extraction_succesful (bool): Indicates if extraction met quality threshold
                                       Based on confidence scores or validation rules
        
        confident_value (float | None): AI confidence score (0.0 to 1.0)
                                       None for deterministic methods
                                       >0.8: High confidence
                                       0.5-0.8: Medium confidence
                                       <0.5: Low confidence (may trigger is_extraction_succesful=False)
        
        extraction_method (str): Method identifier for tracking/debugging
                                "hybrid": Deterministic + AI (Camelot + Mistral, PDF + Vision)
                                "ai": Pure AI extraction (Mistral vision)
                                "deterministic": Pure geometric/rule-based (Voronoi)
        
        result (str | dict | list): Extracted data in format appropriate to content type
                                   BOQ: dict with sections and items
                                   Gantt: dict with tasks and timeline
                                   Floor plan: dict with rooms and adjacencies
                                   Error: dict with error message
    
    Example:
        {
            "input_format": "application/pdf",
            "is_extraction_succesful": true,
            "confident_value": 0.87,
            "extraction_method": "hybrid",
            "result": {
                "Sections": [...],
                "confidence": 0.87
            }
        }
    """
    input_format: str
    is_extraction_succesful: bool
    confident_value: float | None
    extraction_method: str
    result: str | dict | list 


class ContentType(str, Enum):
    """
    Enumeration of available floor plan extraction modes.
    
    Different modes use different algorithms and have different file type requirements.
    Allows clients to choose extraction strategy based on their needs.
    
    Values:
        titleblock_hybrid: Extract title block metadata (project info, scale, dates)
                          Uses OCR + Vision AI hybrid approach
                          Accepts: PDF or Image
                          Best for: Title blocks with mixed text/graphics
        
        plan_deterministic: Extract room adjacencies using geometric Voronoi method
                           Uses PDF text extraction + Voronoi tessellation
                           Accepts: PDF only (requires text layer)
                           Best for: Well-labeled floor plans, production reliability
        
        plan_ai: Extract room adjacencies using pure AI vision
                Accepts: PDF or Image
                Best for: Unlabeled plans, sketches, photos of drawings
        
        full_result: Extract complete floor plan metadata (rooms + title block)
                    Uses hybrid deterministic + AI approach
                    Accepts: PDF only
                    Best for: Comprehensive extraction in single API call
    """
    titleblock = "titleblock-hybrid"
    plan_deterministic = "rooms-deterministic"
    plan_ai = "rooms-ai"
    full_result = "full-plan-ai"


class ChartFormat(str, Enum):
    """
    Enumeration of Gantt chart layout formats.
    
    Different Gantt chart formats require different parsing strategies.
    Visual charts need bar position inference, tabular charts have explicit dates.
    
    Values:
        visual: Gantt chart where timing is inferred from bar positions
               Layout: Activities listed on left, timeline across top, bars show duration
               Parsing: Computer vision to detect bar start/end positions
               Best for: Traditional graphical Gantt charts, MS Project screenshots
        
        tabular: Gantt chart with structured table including explicit date columns
                Layout: Table with columns like "Task", "Start", "End", "Duration"
                Parsing: Table extraction + date parsing
                Best for: Spreadsheet-based schedules, Primavera P6 exports
        
        full_ai: Use pure AI vision for comprehensive analysis (experimental)
                Parsing: Vision model analyzes entire chart holistically
                Best for: Non-standard layouts, complex dependencies
    """
    visual = "visual"
    tabular = "tabular"
    full_ai = "full ai"


# =============================================================================
# API DOCUMENTATION AND CONFIGURATION
# =============================================================================

description = """
This API helps you to convert your Construction Document into structured JSON files, ideal for further applications and LLM usage.

## Financial Parser

upload and parse **Bill of Quantities**.

## Program Parser

upload and parse **Gantt Charts**.

Please use the parameter chartFormat

"chartFormat (string) – Specifies the layout of the Gantt chart. 
"visual": for charts where activity timing must be inferred from bar positions (with activities on the left and a timeline above)
"tabular": for charts that include a structured table with explicit start, end, and duration fields

## Drawing Parser

upload and parse **Floor Plans**.
"""


# Initialize FastAPI application with metadata
app = FastAPI(
    title="Construction Document Parser for LLM based AI assistants",
    description=description
)


# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# Note: after installation of fastapi run -- fastapi dev main.py -- in terminal to start server locally 
# Go to http://127.0.0.1:8000/docs to view the automatically created API docs

# Configure CORS (Cross-Origin Resource Sharing) middleware
# Allows frontend applications to make requests to this API
app.add_middleware(
    CORSMiddleware,
    # Allow requests from these origins only (security measure)
    allow_origins=[
        "http://localhost:3000",  # Local development frontend (React/Next.js typical port)
        "https://construction-doc-parser.onrender.com"  # Production deployment
    ],
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],     # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],     # Allow all headers (Content-Type, Authorization, etc.)
)


# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/")
async def hello_world():
    """
    Root endpoint providing API information and navigation.
    
    Returns basic API metadata and directs users to interactive documentation.
    Useful for health checks and API discovery.
    
    Returns:
        dict: Welcome message and link to docs
    
    Example:
        GET http://localhost:8000/
        Response:
        {
            "This is": "Document Parser for LLM based AI assistants",
            "To try out API": "Go to -> /docs"
        }
    """
    return {
        "This is": "Document Parser for LLM based AI assistants",
        "To try out API": "Go to -> /docs"
    }


# =============================================================================
# GANTT CHART PARSER ENDPOINT
# =============================================================================

@app.post("/gantt_parser/{chart_format}")
async def create_upload_file_gantt(file: UploadFile, chart_format: ChartFormat):
    """
    Parse Gantt chart from uploaded file and extract project schedule data.
    
    Supports two chart formats:
    - Visual: Traditional graphical Gantt (bars represent time)
    - Tabular: Table-based schedule with explicit date columns
    
    Processing Pipeline:
    1. Validate file type (must be PDF)
    2. Save uploaded file temporarily with unique filename
    3. Parse Gantt chart based on specified format
    4. Return structured JSON with tasks, dates, dependencies
    5. Cleanup: Delete temporary file
    
    Args:
        file (UploadFile): Uploaded PDF file containing Gantt chart
        chart_format (ChartFormat): Layout format ("visual" or "tabular")
    
    Returns:
        Response: Standardized response with extracted schedule data
            result format:
            {
                "tasks": [
                    {
                        "id": "1",
                        "name": "Foundation Work",
                        "start": "2024-01-15",
                        "end": "2024-02-28",
                        "duration": 44,
                        "dependencies": []
                    }
                ],
                "project_info": {...}
            }
    
    Raises:
        HTTPException 400: If file is not a PDF
        HTTPException 500: If processing fails (corrupted PDF, parsing error)
    
    Example:
        curl -X POST "http://localhost:8000/gantt_parser/visual" \
             -F "file=@project_schedule.pdf"
    
    Note:
        - Only PDFs accepted (images not supported for Gantt parsing)
        - File automatically deleted after processing (no storage)
        - Large files may take 10-30 seconds to process
    """
    # Create upload directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = None  # Track file path for cleanup in finally block
    
    try:
        # =====================================================================
        # VALIDATION: Ensure file is PDF
        # =====================================================================
        if not (file.content_type == 'application/pdf'):
            raise HTTPException(
                status_code=400, 
                detail="File must be a PDF"
            )
        
        # =====================================================================
        # FILE HANDLING: Generate unique filename and save
        # =====================================================================
        
        # Extract file extension (should be .pdf)
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
        
        # Generate unique filename using UUID to prevent collisions
        # Important for concurrent requests
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Read uploaded file content into memory
        file_content = await file.read()
        
        # Save PDF to disk
        # Note: For images, code includes conversion logic (currently unreachable due to PDF-only validation)
        if file.content_type == 'application/pdf':
            with open(file_path, 'wb') as f:
                f.write(file_content)
        else:
            # Image handling (unreachable code - kept for future extensibility)
            with Image.open(io.BytesIO(file_content)) as im:
                # Convert RGBA/P images to RGB for JPEG compatibility
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
                im.save(file_path, 'JPEG')
        
        # =====================================================================
        # PARSING: Extract Gantt chart data
        # =====================================================================
        
        # Call appropriate parser based on chart format
        # Returns: (result_dict, method_str, is_successful_bool)
        result, method, is_succesful = gantt_parser.parse_gantt_chart(file_path, chart_format)

        # =====================================================================
        # RESPONSE CONSTRUCTION
        # =====================================================================
        
        response = Response(
            input_format=file.content_type,  # "application/pdf"
            is_extraction_succesful=is_succesful,  # Based on parser validation
            confident_value=None,  # Gantt parsing doesn't use AI confidence scores
            extraction_method=method,  # "visual" or "tabular"
            result=result  # Structured schedule data
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors) without modification
        raise
    except Exception as e:
        # Catch all other errors and return 500 with error details
        print(f"Error processing file: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing file: {str(e)}"
        )
    finally:
        # =====================================================================
        # CLEANUP: Always delete temporary file
        # =====================================================================
        # Ensures no disk space leaks even if errors occur
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        gc.collect()  # Force garbage collection to free memory


# =============================================================================
# BILL OF QUANTITIES (BOQ) PARSER ENDPOINT
# =============================================================================

@app.post("/financial_parser/")
async def create_upload_file_fin(file: UploadFile):
    """
    Parse Bill of Quantities (BOQ) from uploaded PDF and extract cost data.
    
    Uses hybrid Camelot + Mistral AI approach:
    1. Camelot extracts raw tables (deterministic, reliable)
    2. Mistral AI structures and validates data (intelligent, context-aware)
    
    Processing Pipeline:
    1. Validate file type (PDF only)
    2. Save uploaded file temporarily
    3. Extract tables with Camelot
    4. Structure data with Mistral AI
    5. Validate extraction quality (confidence > 0.5)
    6. Return structured JSON
    7. Cleanup temporary file
    
    Args:
        file (UploadFile): Uploaded PDF file containing BOQ tables
    
    Returns:
        Response: Standardized response with extracted BOQ data
            result format:
            {
                "Sections": [
                    {
                        "section_name": "Earthwork",
                        "items": [
                            {
                                "position": "1.1",
                                "description": "Excavation",
                                "quantity": 100,
                                "unit": "m³",
                                "unit_price": 45.50,
                                "total": 4550.00
                            }
                        ]
                    }
                ],
                "confidence": 0.87
            }
    
    Raises:
        HTTPException 400: If file is not PDF or image
        HTTPException 500: If processing fails
    
    Example:
        curl -X POST "http://localhost:8000/financial_parser/" \
             -F "file=@bill_of_quantities.pdf"
    
    Note:
        - confidence_value returned indicates AI extraction quality
        - is_extraction_succesful = True only if confidence > 0.5
        - For critical financial docs, manually verify high-value items
    """
    # Create upload directory
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = None
    
    try:
        # =====================================================================
        # VALIDATION: PDF or image
        # =====================================================================
        # Note: Current implementation only processes PDFs
        # Image handling is validated but not implemented in boq module
        if not (file.content_type == 'application/pdf' or file.content_type.startswith('image/')):  # type: ignore
            raise HTTPException(
                status_code=400, 
                detail="File must be a PDF or image"
            )
        
        # =====================================================================
        # FILE HANDLING: Save uploaded file
        # =====================================================================
        
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        file_content = await file.read()
        
        # Save PDF (images not currently processed by BOQ module)
        if file.content_type == 'application/pdf':
            with open(file_path, 'wb') as f:
                f.write(file_content)

        # =====================================================================
        # PARSING: Extract BOQ data
        # =====================================================================
        
        # Note: financial_boq() is commented out (stub function)
        # Using extract_boq_mistral() which implements hybrid Camelot + Mistral approach
        # result, method, is_succesful = boq.financial_boq(file_path)  # Stub
        result, method, is_succesful, confidence = boq.extract_boq_mistral(file_path)
        
        # =====================================================================
        # RESPONSE CONSTRUCTION
        # =====================================================================
        
        response = Response(
            input_format=file.content_type,
            is_extraction_succesful=is_succesful,  # True if confidence > 0.5
            confident_value=confidence,  # AI confidence score (0.0-1.0)
            extraction_method=method,  # "hybrid" (Camelot + Mistral)
            result=result  # Structured BOQ data or error dict
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing file: {str(e)}"
        )
    finally:
        # =====================================================================
        # CLEANUP
        # =====================================================================
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        gc.collect()


# =============================================================================
# FLOOR PLAN PARSER ENDPOINT
# =============================================================================

@app.post("/drawing_parser/{content_type}/")
async def create_upload_file_floorplans(file: UploadFile, content_type: ContentType):
    """
    Parse floor plan and extract metadata based on specified content type.
    
    Supports multiple extraction modes with different requirements:
    
    1. titleblock-hybrid: Extract title block info (project name, scale, date)
       - Accepts: PDF or Image
       - Method: OCR + Vision AI hybrid
       - PDF converted to image for processing
    
    2. rooms-deterministic: Extract room adjacencies using Voronoi geometry
       - Accepts: PDF only (requires text layer)
       - Method: PDF text extraction + Voronoi tessellation
       - Most reliable for well-labeled plans
    
    3. rooms-ai: Extract room adjacencies using pure AI vision
       - Accepts: PDF or Image
       - Method: Mistral vision model
       - Best for unlabeled plans, sketches
    
    4. full-plan-ai: Extract complete floor plan data (rooms + title block)
       - Accepts: PDF only
       - Method: Hybrid (Voronoi + AI)
       - Comprehensive extraction in single call
    
    Processing Pipeline:
    1. Validate file type based on content_type
    2. Save/convert file as needed
    3. Call appropriate parser
    4. Return structured JSON
    5. Cleanup temporary files
    
    Args:
        file (UploadFile): Floor plan file (PDF or image based on content_type)
        content_type (ContentType): Extraction mode/strategy
    
    Returns:
        Response: Standardized response with extracted floor plan data
            Format varies by content_type:
            
            titleblock-hybrid:
            {
                "projectName": "Residential Building A",
                "scale": "1:100",
                "date": "2024-01-15",
                "confidence": 0.92
            }
            
            rooms-deterministic or rooms-ai:
            {
                "Kitchen": ["Living Room", "Dining Room"],
                "Bedroom": ["Bathroom", "Hallway"],
                ...
            }
            
            full-plan-ai:
            {
                "titleBlock": {...},
                "roomAdjacency": {...}
            }
    
    Raises:
        HTTPException 400: If file type doesn't match content_type requirements
        HTTPException 500: If processing fails
    
    Example:
        # Extract room adjacencies with Voronoi (deterministic)
        curl -X POST "http://localhost:8000/drawing_parser/rooms-deterministic/" \
             -F "file=@floorplan.pdf"
        
        # Extract room adjacencies with AI (handles unlabeled plans)
        curl -X POST "http://localhost:8000/drawing_parser/rooms-ai/" \
             -F "file=@sketch.jpg"
    
    Note:
        - Deterministic method requires labeled rooms in PDF
        - AI method can handle images but may hallucinate on complex plans
        - PDF to image conversion happens automatically for titleblock-hybrid
        - Both original and converted files cleaned up automatically
    """
    # Create upload directory
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = None  # Original uploaded file path
    converted_image_path = None  # Track PDF->image conversion separately
    
    try:
        # =====================================================================
        # VALIDATION: File type based on content_type requirements
        # =====================================================================
        
        # rooms-deterministic and full-plan-ai require PDF (need text layer)
        if content_type in ["rooms-deterministic", "full-plan-ai"]:
            if not file.content_type == 'application/pdf':
                raise HTTPException(
                    status_code=400, 
                    detail="Deterministic or Hybrid plan parsing requires PDF file"
                )
        
        # titleblock-hybrid accepts both image and PDF
        # PDF will be converted to image for OCR processing
        elif content_type == "titleblock-hybrid":
            if not (file.content_type.startswith('image/') or file.content_type == 'application/pdf'):
                raise HTTPException(
                    status_code=400, 
                    detail="Titleblock Hybrid parsing requires Image or PDF file"
                )
        
        # rooms-ai accepts both (AI vision works with images directly)
        elif content_type == "rooms-ai":
            if not (file.content_type.startswith('image/') or file.content_type == 'application/pdf'):
                raise HTTPException(
                    status_code=400, 
                    detail="File must be an image or PDF"
                )
        
        # Fallback: images only (future content types)
        else:
            if not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400, 
                    detail="File must be an image"
                )
        
        # =====================================================================
        # FILE HANDLING: Save and potentially convert
        # =====================================================================
        
        # Determine file extension
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Read file content
        file_content = await file.read()
        
        # Handle PDF files
        if file.content_type == 'application/pdf':
            # Special case: titleblock-hybrid needs image, so convert PDF->image
            if content_type == "titleblock-hybrid":
                # Step 1: Save PDF temporarily
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                
                # Step 2: Convert first page of PDF to image
                # helper.convert_pdf2img returns list of image paths
                converted_image_paths = helper.convert_pdf2img(file_path, pages=(0,))

                # Step 3: Extract single image path from list
                if isinstance(converted_image_paths, list) and len(converted_image_paths) > 0:
                    converted_image_path = converted_image_paths[0]  # First page
                else:
                    converted_image_path = converted_image_paths

                # Use converted image for titleblock processing
                processing_file_path = converted_image_path
            else:
                # For other content types: Use PDF directly
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                processing_file_path = file_path
        else:
            # Handle image files: Save as JPEG with RGB conversion
            with Image.open(io.BytesIO(file_content)) as im:
                # Convert RGBA (transparency) and P (palette) to RGB
                # Required for JPEG format compatibility
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
                im.save(file_path, 'JPEG')
            processing_file_path = file_path
        
        # =====================================================================
        # PARSING: Call appropriate parser based on content_type
        # =====================================================================
        
        # Initialize default values
        method = "None"
        is_succesful = False
        confidence = None
        
        # Route to appropriate parser
        if content_type == "titleblock-hybrid":
            # Extract title block: project info, scale, architect, dates
            # Uses OCR + Vision AI hybrid
            # Returns: (result_dict, method_str, is_successful_bool, confidence_float)
            result, method, is_succesful, confidence = floorplan_parser.get_title_block_info(processing_file_path)
            
        elif content_type == "rooms-deterministic":
            # Extract room adjacencies using Voronoi tessellation
            # Deterministic method: no confidence score
            # Returns: dict mapping rooms to neighbor lists
            result = vor.neighboring_rooms_voronoi(processing_file_path)
            method = "deterministic"
            is_succesful = True  # Deterministic methods don't have confidence thresholds
            confidence = None  # No AI involved, no confidence score
            
        elif content_type == "rooms-ai":
            # Extract room adjacencies using pure AI vision
            # Can handle unlabeled plans and images
            # Returns: (result_dict, method_str, is_successful_bool, confidence_float)
            result, method, is_succesful, confidence = full.get_neighbouring_rooms_with_ai(processing_file_path)
            
        elif content_type == "full-plan-ai":
            # Extract complete floor plan: title block + room adjacencies
            # Uses hybrid approach (Voronoi for rooms, AI for context)
            # Returns: dict with nested titleBlock and roomAdjacency
            result = vor.extract_full_floorplan(processing_file_path)
            method = "hybrid"
            is_succesful = True
            confidence = None  # Hybrid method doesn't return single confidence score
            
        # =====================================================================
        # RESPONSE CONSTRUCTION
        # =====================================================================
        
        response = Response(
            input_format=file.content_type,  # Original MIME type (before conversion)
            is_extraction_succesful=is_succesful,  # Based on confidence or deterministic success
            confident_value=confidence,  # AI confidence (None for deterministic)
            extraction_method=method,  # "hybrid", "deterministic", or "ai"
            result=result  # Extracted floor plan data
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing file: {str(e)}"
        )
    finally:
        # =====================================================================
        # CLEANUP: Remove both original and converted files
        # =====================================================================
        # Important: titleblock-hybrid creates two files (PDF + converted image)
        # Both must be cleaned up to prevent disk space leaks
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        if converted_image_path and os.path.exists(converted_image_path):
            os.remove(converted_image_path)
        gc.collect()  # Force garbage collection
    

# =============================================================================
# AI CHATBOT ENDPOINT
# =============================================================================

@app.post("/ask_ai/")
async def ask_ai(request: Request):
    """
    Query parsed construction document data using natural language AI assistant.
    
    Allows users to ask questions about previously parsed documents without
    manually navigating JSON structures. Uses GPT-4o-mini for cost-effective
    question answering with document context.
    
    Workflow:
    1. Receive question + parsed document data
    2. Construct prompt with document context
    3. Call OpenAI GPT-4o-mini
    4. Return answer + token usage stats
    
    Use Cases:
    - "What is the total project cost?"
    - "List all tasks starting in March"
    - "Which rooms are adjacent to the kitchen?"
    - "What is the scale of this drawing?"
    - "How many line items are in section 3?"
    
    Args:
        request (Request): JSON body with:
            {
                "question": "What is the total cost?",
                "document_data": {
                    "Sections": [...],
                    "confidence": 0.85
                }
            }
    
    Returns:
        dict: AI response with usage statistics
            {
                "answer": "The total project cost is €1,234,567.89",
                "model": "gpt-4o-mini",
                "usage": {
                    "prompt_tokens": 1523,
                    "completion_tokens": 45,
                    "total_tokens": 1568
                }
            }
    
    Raises:
        HTTPException 400: If question or document_data missing
        HTTPException 500: If OpenAI API call fails
    
    Example:
        curl -X POST "http://localhost:8000/ask_ai/" \
             -H "Content-Type: application/json" \
             -d '{
                "question": "What rooms are adjacent to the kitchen?",
                "document_data": {"Kitchen": ["Living Room", "Dining"]}
             }'
    
    Note:
        - Answers based ONLY on provided document data (no external knowledge)
        - Token usage returned for cost tracking
        - Temperature=0.7 balances accuracy and natural language
        - Max 500 tokens keeps responses concise and cost-effective
    """
    try:
        # =====================================================================
        # INPUT VALIDATION
        # =====================================================================
        
        # Parse JSON request body
        data = await request.json()
        question = data.get("question")
        document_data = data.get("document_data")
        
        # Validate required fields
        if not question:
            raise HTTPException(
                status_code=400, 
                detail="Missing 'question' field"
            )
        
        if not document_data:
            raise HTTPException(
                status_code=400, 
                detail="Missing 'document_data' field"
            )
        
        # =====================================================================
        # PROMPT CONSTRUCTION
        # =====================================================================
        
        # Create context-aware prompt
        # Key elements:
        # 1. Role definition: "helpful assistant analyzing construction documents"
        # 2. Document context: Full parsed JSON data
        # 3. User question
        # 4. Strict instructions: Answer ONLY from provided data
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

        # =====================================================================
        # OPENAI API CALL
        # =====================================================================
        
        # Call GPT-4o-mini for cost-effective question answering
        # Alternative models:
        # - gpt-4o: More accurate but more expensive
        # - gpt-3.5-turbo: Cheaper but less capable
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Optimized for cost/performance balance
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,  # Limit response length (cost control)
                            # Increase for detailed reports
                            # Decrease for simple queries
            temperature=0.7  # Balanced creativity/accuracy
                            # Lower (0.3): More factual, less natural
                            # Higher (0.9): More creative, less precise
        )
        
        # Extract answer from response
        answer = response.choices[0].message.content
        
        # =====================================================================
        # RESPONSE CONSTRUCTION
        # =====================================================================
        
        # Return answer + metadata for tracking
        return {
            "answer": answer,
            "model": "gpt-4o-mini",
            "usage": {
                # Token usage for cost calculation
                # Pricing (as of 2024):
                # - Input: $0.150 per 1M tokens
                # - Output: $0.600 per 1M tokens
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
    except Exception as e:
        # =====================================================================
        # ERROR HANDLING
        # =====================================================================
        print(f"Error in ask_ai: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=str(e)
        )
        gc.collect()  # Cleanup on error


# =============================================================================
# PERFORMANCE OPTIMIZATION NOTES
# =============================================================================

# Future optimization considerations:
# https://fastapi.tiangolo.com/async/#in-a-hurry
#
# Current implementation uses:
# - async/await for I/O operations (file uploads, API calls)
# - Synchronous processing for CPU-intensive tasks (PDF parsing, Voronoi)
#
# Potential improvements:
# 1. Use asyncio.gather() for parallel processing when handling multiple files
# 2. Implement background tasks for long-running extractions (FastAPI BackgroundTasks)
# 3. Add Redis caching for frequently requested documents
# 4. Use connection pooling for database operations (if added)
# 5. Implement rate limiting to prevent API abuse
# 6. Add request queuing for resource-intensive operations