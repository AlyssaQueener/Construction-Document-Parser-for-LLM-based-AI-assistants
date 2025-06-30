from typing import Union

from fastapi import FastAPI, UploadFile

app = FastAPI()

## after installation of fastapi run -- fastapi dev main.py -- in terminal to start server locally 
## go to http://127.0.0.1:8000/docs to view the automatically created api docs

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/drawingparser/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename, "filetype:": file.content_type}