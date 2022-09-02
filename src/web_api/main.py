import os
import binascii
import aiohttp
from fastapi import FastAPI, BackgroundTasks, UploadFile, Request, Form
from fastapi.responses import  HTMLResponse, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from starlette.middleware.sessions import SessionMiddleware
import views

app = FastAPI()
HOST = os.environ.get('HOST')
MONGO_HOST = os.environ.get('MONGO_HOST')
MONGO_PORT = os.environ.get('MONGO_PORT')
AUTH_HOST = os.environ.get('AUTH_HOST')
AUTH_PORT = os.environ.get('AUTH_PORT')

@app.on_event('startup')
async def get_mongo():
    video_db = AsyncIOMotorClient(f'mongodb://{MONGO_HOST}:{MONGO_PORT}').video
    app.library = video_db.library
    app.fs = AsyncIOMotorGridFSBucket(video_db)

@app.get('/')
async def index():
    return HTMLResponse(views.sign_up_login_block)

@app.post('/sign-up')
async def sign_up(email: str = Form(), password: str = Form()):
    user_data = {'email': email, 'password': password}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://{AUTH_HOST}:{AUTH_PORT}/sign-up', data=user_data) as response:
                r = await response.text()
    except Exception as e:
        return HTMLResponse(f'<h3>Error: {str(e)}</h3>{views.sign_up_login_block}')

    if '1' in r:
        return HTMLResponse(f'<h3>An account already exists with that email</h3>{views.sign_up_login_block}')
    return HTMLResponse(views.sign_up_login_block)

@app.post('/login')
async def login(request: Request, email: str = Form(), password: str = Form()):
    user_data = {'email': email, 'password': password}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://{AUTH_HOST}:{AUTH_PORT}/login', data=user_data) as response:
                r = await response.text()
                print(r)
    except Exception as e:
        return HTMLResponse(f'<h3>Error: {str(e)}</h3>{views.sign_up_login_block}')

    if '1' in r:
        return HTMLResponse(f'<h3>Login failed</h3>{views.sign_up_login_block}')
    request.session['email'] = email
    videos = await _get_videos(request)
    return HTMLResponse(f'<h3>Logged in as "{email}"</h3>{views.upload_block}{videos}{views.logout_block}')

@app.get('/logout')
async def logout(request: Request):
    request.session['email'] = None
    return HTMLResponse(views.sign_up_login_block)

async def _generate_hash():
    return binascii.hexlify(os.urandom(16)).decode('utf-8')

async def _add_library_record(email: str, hash: str):
    data = {'email': email, 'filename': hash}
    await app.library.insert_one(data)

async def _upload(file: object, hash: str):
    grid_in = app.fs.open_upload_stream(
        hash, metadata={'contentType': 'video/mp4'})
    data = await file.read()
    await grid_in.write(data)
    await grid_in.close()  # uploaded on close

@app.post('/upload')
async def upload(request: Request, file: UploadFile, background_tasks: BackgroundTasks):
    if request.session['email']:
        if file.filename:
            hash = await _generate_hash()
            background_tasks.add_task(_upload, file, hash)
            background_tasks.add_task(_add_library_record, request.session['email'], hash)
            videos = await _get_videos(request)
            return HTMLResponse(f'{views.upload_block}{videos}{views.logout_block}')
        return HTMLResponse(f'<h3>Please select a file to upload</h3>{views.upload_block + views.logout_block}')
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

async def _get_videos(request: object):
    videos = app.library.find({'email': request.session['email']})
    docs = await videos.to_list(None)
    video_urls = ''
    for i in docs:
        filename = i['filename']
        v = f'<a href="http://{HOST}/stream/{filename}" target="_blank">http://{HOST}/stream/{filename}</a>'
        video_urls = video_urls + '<br>' + v
    return video_urls

app.add_middleware(SessionMiddleware, secret_key='abc')
