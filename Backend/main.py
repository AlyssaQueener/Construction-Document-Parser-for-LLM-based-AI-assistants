from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, HTTPException, Request
from PIL import Image 
import src.plan2data.titleBlockInfo as floorplan_parser
import io
import os
import uuid
import src.gantt2data.ganttParser as gantt_parser
#import boq2data_gemini as boq  # COMMENTED OUT - Missing module
from pydantic import BaseModel
from openai import OpenAI
import json

# ========================================
# OPENAI API KEY - PUT YOUR KEY HERE
# ========================================
OPENAI_API_KEY = "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"  # ← REPLACE THIS WITH YOUR ACTUAL KEY

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

class Response(BaseModel):
    input_format: str
    is_extraction_succesful: bool
    confident_value: float | None
    extraction_method: str
    result: str | dict | list 

description = """
This API helps you to convert your Construction Document into structured JSON files, ideal for further applications and LLM usage.

## Financial Parser
upload and parse **Bill of Quantities**.

## Program Parser
upload and parse **Gantt Charts**.

Please use the parameter chartFormat:
- "visual": for charts where activity timing must be inferred from bar positions (with activities on the left and a timeline above)
- "tabular": for charts that include a structured table with explicit start, end, and duration fields

## Drawing Parser
upload and parse **Floor Plans**.

## AI Assistant
Ask questions about your parsed documents using AI.
"""

app = FastAPI(
    title="Construction Document Parser for LLM based AI assistants",
    description=description
)

## after installation of fastapi run -- fastapi dev main.py -- in terminal to start server locally 
## go to http://127.0.0.1:8000/docs to view the automatically created api docs

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def hello_world():
    return {"This is": "Document Parser for LLM based AI assistants",
            "To try out API" : "Go to -> /docs"
            }

# ========================================
# GANTT PARSER
# ========================================
@app.post("/gantt_parser/{chart_format}")
async def create_upload_file_gantt(file: UploadFile, chart_format):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
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
        
        result, method, is_succesful = gantt_parser.parse_gantt_chart(file_path, chart_format)

        response = Response(
            input_format=file.content_type,  
            is_extraction_succesful=is_succesful,
            confident_value=None,
            extraction_method=method,
            result=result
        )
        
        os.remove(file_path)  
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# ========================================
# FINANCIAL PARSER - COMMENTED OUT
# ========================================
# @app.post("/financial_parser/")
# async def create_upload_file_fin(file: UploadFile):
#     upload_dir = "uploads"
#     os.makedirs(upload_dir, exist_ok=True)
#     try:
#         if not (file.content_type == 'application/pdf' or file.content_type.startswith('image/')):
#             raise HTTPException(status_code=400, detail="File must be a PDF or image")
#         
#         file_extension = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
#         unique_filename = f"{uuid.uuid4()}{file_extension}"
#         file_path = os.path.join(upload_dir, unique_filename)
#         
#         file_content = await file.read()
#         
#         if file.content_type == 'application/pdf':
#             with open(file_path, 'wb') as f:
#                 f.write(file_content)
#
#         result, method, is_success = boq.financial_boq(file_path)
#
#         response = Response(
#             input_format=file.content_type,  
#             is_extraction_succesful=is_success,
#             confident_value=None,
#             extraction_method=method,
#             result=result
#         )
#         
#         os.remove(file_path)  
#         
#         return response
#         
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error processing file: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# ========================================
# DRAWING PARSER (Floor Plans)
# ========================================
@app.post("/drawing_parser/")
async def create_upload_file_floorplans(file: UploadFile):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        file_content = await file.read()
        
        with Image.open(io.BytesIO(file_content)) as im:
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            im.save(file_path, 'JPEG')
        
        method = "None"
        is_succesful = False

        result, method, is_succesful, confidence = floorplan_parser.get_title_block_info(file_path)

        response = Response(
            input_format=file.content_type,  
            is_extraction_succesful=is_succesful,
            confident_value=confidence,
            extraction_method=method,
            result=result
        )
        
        os.remove(file_path)  
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# ========================================
# AI CHATBOT (OpenAI)
# ========================================
@app.post("/ask_ai/")
async def ask_ai(request: Request):
    """
    Ask AI questions about parsed construction document data.
    No conversation memory - each question is independent.
    
    Example request body:
    {
        "question": "What is the project location?",
        "document_data": { ... parsed JSON data ... }
    }
    """
    try:
        data = await request.json()
        question = data.get("question")
        document_data = data.get("document_data")
        
        if not question:
            raise HTTPException(status_code=400, detail="Missing 'question' field")
        
        if not document_data:
            raise HTTPException(status_code=400, detail="Missing 'document_data' field")
        
        # Create prompt with document data
        prompt = f"""You are a helpful assistant analyzing construction document data.

Here is the parsed construction document data in JSON format:
{json.dumps(document_data, indent=2)}

User question: {question}

Instructions:
- Answer the question based ONLY on the data provided above
- Be concise and specific
- If the information is not in the data, say "This information is not available in the parsed document"
- Focus on construction-related insights
- Use professional terminology

Answer:"""

        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Cheapest model - $0.0004 per question
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract answer
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

#https://fastapi.tiangolo.com/async/#in-a-hurry maybe have a look at this to improve performance