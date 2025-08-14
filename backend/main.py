from fastapi import FastAPI
app = FastAPI()

@app.get('/')
async def root():
    """
    só um hello word
    """
    return {'message': 'Hello World'}