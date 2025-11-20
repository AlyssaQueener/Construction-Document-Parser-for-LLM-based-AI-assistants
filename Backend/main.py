from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, HTTPException, Request
from PIL import Image 
import src.plan2data.titleBlockInfo as floorplan_parser
import io
import os
import uuid
import src.gantt2data.ganttParser as gantt_parser
import boq2data_gemini as boq
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("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"))

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

Please use the parameter chartFormat

"chartFormat (string) – Specifies the layout of the Gantt chart. 
"visual": for charts where activity timing must be inferred from bar positions (with activities on the left and a timeline above)
"tabular": for charts that include a structured table with explicit start, end, and duration fields

## Drawing Parser

upload and parse **Floor Plans**.
"""

app = FastAPI(
    title="Construction Document Parser",
    description=description,
    version="1.0.0"
)

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
        
        result, method, is_succesful = gantt_parser.parse_gantt_chart(file_path,chart_format)

        response = Response(
            input_format=file.content_type,  
            is_extraction_succesful= is_succesful,
            extraction_method=method,
            result=result,
            confident_value=None
        )
        
        os.remove(file_path)  
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/financial_parser/")
async def create_upload_file_fin(file: UploadFile):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    try:
        if not (file.content_type == 'application/pdf' or file.content_type.startswith('image/')):
            raise HTTPException(status_code=400, detail="File must be a PDF or image")
        
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        file_content = await file.read()
        
        if file.content_type == 'application/pdf':
            with open(file_path, 'wb') as f:
                f.write(file_content)

        result, method, is_success = boq.financial_boq(file_path)

        response = Response(
            input_format=file.content_type,  
            is_extraction_succesful= is_success,
            extraction_method=method,
            result=result,
            confident_value=None
        )
        
        os.remove(file_path)  
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

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
            is_extraction_succesful= is_succesful,
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

@app.post("/ask_ai/")
async def ask_ai(request: Request):
    """
    Ask AI questions about parsed construction document data.
    No conversation memory - each question is independent.
    """
    try:
        data = await request.json()
        question = data.get("question")
        document_data = data.get("document_data")
        
        if not question:
            raise HTTPException(status_code=400, detail="Missing question")
        
        if not document_data:
            raise HTTPException(status_code=400, detail="Missing document_data")
        
        # Create prompt with document data
        prompt = f"""You are a helpful assistant analyzing construction document data.

Here is the parsed construction document data in JSON format:
{json.dumps(document_data, indent=2)}

User question: {question}

Instructions:
- Answer the question based on the data provided
- Be concise and specific
- If the information is not in the data, say so politely
- Focus on construction-related insights

Answer:"""

        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
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