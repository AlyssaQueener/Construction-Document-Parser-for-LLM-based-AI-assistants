from typing import Union

from fastapi import FastAPI, UploadFile, HTTPException
from PIL import Image 
import testWorkflowFloorplanForApi as floorplan_parser
import io
import os
import uuid

app = FastAPI()

## after installation of fastapi run -- fastapi dev main.py -- in terminal to start server locally 
## go to http://127.0.0.1:8000/docs to view the automatically created api docs

@app.get("/financialparser")
def read_root():
    return {"Under": "construction"}
@app.get("/documentparser")
def read_root():
    return {"Under": "construction"}
@app.post("/drawingparser/uploadfile/")
async def create_upload_file_v2(file: UploadFile):
    upload_dir = "uploads"  # Make sure this directory exists
    os.makedirs(upload_dir, exist_ok=True)
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Read and save file
        file_content = await file.read()
        
        with Image.open(io.BytesIO(file_content)) as im:
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            im.save(file_path, 'JPEG')
        
        # Process the image
        result = floorplan_parser.get_title_block_info(file_path)
        
        # Optionally keep the file or remove it after processing
        os.remove(file_path)  # Uncomment to delete after processing
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

#https://fastapi.tiangolo.com/async/#in-a-hurry maybe have a look at this to improve performance