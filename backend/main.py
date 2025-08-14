from typing import Annotated
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.post("/files/")
async def create_files(
    files: Annotated[list[bytes], File(description="Multiple files as bytes")],
):
    return {"file_sizes": [len(file) for file in files]}

#alterando pra salvar o arquivo uplodado
@app.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile] = File(...)):
    try:
        for file in files:
            with open(f"./data/{file.filename}", "wb") as buffer:
                buffer.write(file.file.read())
        return {"filenames": [file.filename for file in files]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.get("/")
async def main():
    content = """
<body>
<form action="/files/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
<form action="/uploadfiles/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)