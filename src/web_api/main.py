import os
import aiohttp
import json
from fastapi import FastAPI, BackgroundTasks, UploadFile, Request, Form
from fastapi.responses import  HTMLResponse, PlainTextResponse, StreamingResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from starlette.middleware.sessions import SessionMiddleware
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
        return HTMLResponse(f'<h3>An account already exists with that email</h3>{views.index}')
    return HTMLResponse(views.index)

@app.post('/login')
async def login(request: Request, email: str = Form(), password: str = Form()):
    user_data = {'email': email, 'password': password}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://{AUTH_HOST}:{AUTH_PORT}/login', data=user_data) as response:
                r = await response.text()
                print(r)
    except Exception as e:
        return HTMLResponse(f'<h3>Error: {str(e)}</h3>{views.index}')

    if '1' in r:
        return HTMLResponse(f'<h3>Login failed</h3>{views.index}')
    request.session['email'] = email
    return HTMLResponse(f'<h3>Logged in as "{email}"</h3>{views.index}')

@app.get('/logout')
async def logout(request: Request):
    request.session['email'] = None
    return HTMLResponse(views.index)

async def _upload(file: object, email: str):
    grid_in = app.fs.open_upload_stream(
        file.filename, metadata={'contentType': 'video/mp4', 'email': email})
    data = await file.read()
    await grid_in.write(data)
    await grid_in.close()  # uploaded on close

@app.post('/upload')
async def upload(request: Request, file: UploadFile, background_tasks: BackgroundTasks):
    if request.session['email']:
        if file.filename:
            background_tasks.add_task(_upload, file, request.session['email'])
            return HTMLResponse(f'<h3><a href="http://localhost/stream/{file.filename}" target="_blank">Play</a></h3>{views.index}')
        return HTMLResponse(f'<h3>Please select a file to upload</h3>{views.index}')
    return HTMLResponse(f'<h3>Please log in</h3>{views.index}')

@app.get('/stream/{filename}')
async def stream(filename: str, request: Request):
    if request.session['email']:
        grid_out = await app.fs.open_download_stream_by_name(filename)
        
        async def read():
            while grid_out.tell() < grid_out.length:
                yield await grid_out.readchunk()

        return StreamingResponse(read(), media_type='video/mp4', 
            headers={'Content-Length': str(grid_out.length)})
    return HTMLResponse(f'<h3>Please log in</h3>{views.index}')

app.add_middleware(SessionMiddleware, secret_key='abc')
