import os
from fastapi.middleware.cors import CORSMiddleware
import gc


os.environ['OMP_NUM_THREADS'] = '1'  # Limit OpenCV threads
os.environ['OPENBLAS_NUM_THREADS'] = '1' 
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
#from voronoi_functions import*
from pydantic import BaseModel
from enum import Enum
# run fastapi dev main.py
#     server   Server started at http://127.0.0.1:8000  server   Documentation at http://127.0.0.1:8000/docs
from openai import OpenAI
import json
from fastapi import Request



# ========================================
# OPENAI API KEY
# ========================================
OPENAI_API_KEY = "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"  
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



app = FastAPI(
    title="Construction Document Parser for LLM based AI assistants",
    description=description
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

@app.get("/")
async def hello_world():
    return {"This is": "Document Parser for LLM based AI assistants",
            "To try out API" : "Go to -> /docs"
            }
########################################## GANT##########################################    
@app.post("/gantt_parser/{chart_format}")
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
@app.post("/financial_parser/")
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

@app.post("/drawing_parser/{content_type}/")
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
@app.post("/ask_ai/")
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