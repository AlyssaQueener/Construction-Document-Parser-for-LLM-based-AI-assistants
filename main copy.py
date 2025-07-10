from typing import Union

from fastapi import FastAPI, UploadFile, HTTPException
from PIL import Image 
import src.plan2data.titleBlockInfo as floorplan_parser
import boq2data_gemini as boq
import io
import os
import uuid
import src.gantt2data.ganttParser as gantt_parser

app = FastAPI()

# after installation of fastapi run -- fastapi dev main.py -- in terminal to start server locally 
# go to http://127.0.0.1:8000/docs to view the automatically created api docs
###################################################################
@app.post("/financial/uploadfile/")

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

        result = boq.financial_boq(file_path)
        os.remove(file_path)  
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
##################################################################
@app.post("/gantt/uploadfile/")
async def create_upload_file_gantt(file: UploadFile):
    upload_dir = "uploads"  # Make sure this directory exists
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
        else:
            with Image.open(io.BytesIO(file_content)) as im:
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
                im.save(file_path, 'JPEG')
        
        
        result = gantt_parser.parse_gantt_chart(file_path)
        
        os.remove(file_path)  
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
@app.get("/documentparser")
def read_root():
    return {"Under": "construction"}
@app.post("/drawingparser/uploadfile/")
async def create_upload_file_v2(file: UploadFile):
    upload_dir = "uploads"  # Make sure this directory exists
    os.makedirs(upload_dir, exist_ok=True)
    
    try:
        if not file.content_type.startswith('image/'): # type: ignore
            raise HTTPException(status_code=400, detail="File must be an image")
        
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        file_content = await file.read()
        
        with Image.open(io.BytesIO(file_content)) as im:
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            im.save(file_path, 'JPEG')
        
        result = floorplan_parser.get_title_block_info(file_path)
        
        os.remove(file_path)  
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

#https://fastapi.tiangolo.com/async/#in-a-hurry maybe have a look at this to improve performance