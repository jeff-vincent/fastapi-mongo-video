import os
import aiohttp
from fastapi import FastAPI, BackgroundTasks, UploadFile, Request, Form
from fastapi.responses import  HTMLResponse, PlainTextResponse
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import StreamingResponse
import views

app = FastAPI()
MONGO_HOST = os.environ.get('MONGO_HOST')
MONGO_PORT = os.environ.get('MONGO_PORT')
AUTH_HOST = os.environ.get('AUTH_HOST')
AUTH_PORT = os.environ.get('AUTH_PORT')

@app.on_event('startup')
async def get_fs():
    video_db = AsyncIOMotorClient(f'mongodb://{MONGO_HOST}:{MONGO_PORT}').video
    app.fs = AsyncIOMotorGridFSBucket(video_db)

@app.get('/')
async def index():
    return HTMLResponse(views.index)

@app.post('/sign-up')
async def sign_up(email: str = Form(), password: str = Form()):
    user_data = {'email': email, 'password': password}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://{AUTH_HOST}:{AUTH_PORT}/sign-up', data=user_data) as response:
                r = await response.text()
    except Exception as e:
        return PlainTextResponse(str(e))

    if '1' in r:
        return 'sign up failed'
    return 'sign up succeeded'

@app.post('/login')
async def login(request: Request, email: str = Form(), password: str = Form()):
    user_data = {'email': email, 'password': password}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://{AUTH_HOST}:{AUTH_PORT}/login', data=user_data) as response:
                r = await response.text()
    except Exception as e:
        return PlainTextResponse(str(e))

    if '1' in r:
        return 'login failed'
    request.session['email'] = email
    return 'login succeeded'

@app.get('/logout')
async def logout(request: Request):
    request.session['username'] = None

    return HTMLResponse(views.index)

async def _upload(file: object):
    grid_in = app.fs.open_upload_stream(
        file.filename, metadata={'contentType': 'video/mp4'})
    data = await file.read()
    await grid_in.write(data)
    await grid_in.close()  # uploaded on close

@app.post('/upload')
async def upload(request: Request, file: UploadFile, background_tasks: BackgroundTasks):
    if request.session['email']:
        background_tasks.add_task(_upload, file)
        return 'uploading'
    return 'upload failed'

@app.get('/stream/{filename}')
async def stream(filename):
    grid_out = await app.fs.open_download_stream_by_name(filename)
    async def read():
        while grid_out.tell() < grid_out.length:
            yield await grid_out.readchunk()

    return StreamingResponse(read(), media_type='video/mp4', 
        headers={'Content-Length': str(grid_out.length)})

app.add_middleware(SessionMiddleware, secret_key='abc')
