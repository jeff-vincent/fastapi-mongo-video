import os
from fastapi import FastAPI, Form
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()
MONGO_HOST = os.environ.get('MONGO_HOST')
MONGO_PORT = os.environ.get('MONGO_PORT')

@app.on_event('startup')
async def get_users():
    users_db = AsyncIOMotorClient(f'mongodb://{MONGO_HOST}:{MONGO_PORT}').users
    app.users = users_db

@app.post('/sign-up')
async def sign_up(email: str = Form(), password: str = Form()):

    data = {'email': email, 'password': password}
    db_user = await app.users.users.find_one({'email': email})
    if db_user:
        return 1
    await app.users.users.insert_one(data)
    return 0

@app.post('/login')
async def login(email: str = Form(), password: str = Form()):
    db_user = await app.users.users.find_one({'email': email})
    if db_user:
        if db_user['password'] == password:
            return 0
    return 1
