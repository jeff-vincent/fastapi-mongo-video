import os
import aiohttp
from fastapi import FastAPI, BackgroundTasks, UploadFile
from fastapi.responses import  HTMLResponse
import uvicorn
import views

app = FastAPI()
USER_IP = os.environ.get('USER_IP')
USER_PORT = os.environ.get('USER_PORT')

@app.get('/')
async def index():
    return HTMLResponse(views.index)

@app.post('/sign-up')
async def sign_up():
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8001/sign-up') as response:
            r = await response.text()

    return HTMLResponse(views.index)

@app.post('/login')
async def login():
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8001/session') as response:
            r = await response.text()
   
    return HTMLResponse(views.index)

async def _upload(file):
    pass

@app.post('/upload')
async def upload(file: UploadFile, background_tasks: BackgroundTasks):
    print(file.filename)
    background_tasks.add_task(_upload, file=file)
    return HTMLResponse(file.filename)

@app.post('/stream')
async def stream():
    pass

if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000)