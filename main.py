from typing import Union

from fastapi import FastAPI, UploadFile, HTTPException
from PIL import Image 
import src.plan2data.titleBlockInfo as floorplan_parser
import io
import os
import uuid
import src.gantt2data.ganttParser as gantt_parser
import boq2data_gemini as boq
from pydantic import BaseModel

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

## Program Parser

upload and parse **Floor Plans and Section Views**.
"""



app = FastAPI(
    title="Construction Document Parser for LLM based AI assistants",
    description=description
)

## after installation of fastapi run -- fastapi dev main.py -- in terminal to start server locally 
## go to http://127.0.0.1:8000/docs to view the automatically created api docs

@app.get("/")
async def hello_world():
    return {"This is": "Document Parser for LLM based AI assistants",
            "To try out API" : "Go to -> /docs"
            }
    
@app.post("/gantt_parser/{chart_format}")
async def create_upload_file_gantt(file: UploadFile, chart_format):
    upload_dir = "uploads"  # Make sure this directory exists
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
            result=result
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
        if not (file.content_type == 'application/pdf' or file.content_type.startswith('image/')): # type: ignore
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
            result=result
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
    upload_dir = "uploads"  # Make sure this directory exists
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

        result, method, is_succesful = floorplan_parser.get_title_block_info(file_path)


        response = Response(
            input_format=file.content_type,  
            is_extraction_succesful= is_succesful,
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

#https://fastapi.tiangolo.com/async/#in-a-hurry maybe have a look at this to improve performance