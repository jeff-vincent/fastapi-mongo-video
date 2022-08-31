import os
import aiohttp
from fastapi import FastAPI, BackgroundTasks, UploadFile, Request
from fastapi.responses import  HTMLResponse
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import StreamingResponse
import uvicorn
import views

app = FastAPI()
AUTH_HOST = os.environ.get('AUTH_HOST')
AUTH_PORT = os.environ.get('AUTH_PORT')
UPLOAD_HOST = os.environ.get('UPLOAD_HOST')
UPLOAD_PORT = os.environ.get('UPLOAD_PORT')

@app.on_event('startup')
async def get_fs():
    video_db = AsyncIOMotorClient('mongodb://localhost:27017').video
    app.fs = AsyncIOMotorGridFSBucket(video_db)

@app.get('/')
async def index():
    return HTMLResponse(views.index)

@app.post('/sign-up')
async def sign_up(request: Request):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'http://{AUTH_HOST}:{AUTH_PORT}/sign-up') as response:
            r = await response.text()

    return HTMLResponse(views.index)

@app.post('/login')
async def login(request: Request):
    
    # async with aiohttp.ClientSession() as session:
    #     async with session.post(f'http://{AUTH_HOST}:{AUTH_PORT}/session') as response:
    #         r = await response.text()
    #         request.session['username'] = r
   
    return HTMLResponse(views.index)

@app.get('/logout')
async def logout(request: Request):
    request.session['username'] = None

    return HTMLResponse(views.index)


async def _upload(file):
    pass

@app.post('/upload')
async def upload(request: Request, file: UploadFile, background_tasks: BackgroundTasks):

    grid_in = app.fs.open_upload_stream(
        file.filename, metadata={'contentType': 'video/mp4'})
    data = await file.read()
    await grid_in.write(data)
    await grid_in.close()  # uploaded on close
    # if request.session['username']:
    #     print(file.filename)
    # else:
    #     print('log in')
    # background_tasks.add_task(_upload, file=file)
    # async with aiohttp.ClientSession() as session:
    #     async with session.post(f'http://{UPLOAD_HOST}:{UPLOAD_PORT}/session') as response:
    #         r = await response.text()
    return HTMLResponse(file.filename)

@app.get('/stream/{filename}')
async def stream(filename):
    grid_out = await app.fs.open_download_stream_by_name(filename)
    async def read():
        while grid_out.tell() < grid_out.length:
            yield await grid_out.readchunk()

    return StreamingResponse(read(), media_type='video/mp4', 
        headers={'Content-Length': str(grid_out.length)})

app.add_middleware(SessionMiddleware, secret_key='abc')

if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8001)