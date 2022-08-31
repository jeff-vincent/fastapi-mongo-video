from fastapi import FastAPI, Form
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn


app = FastAPI()

@app.on_event('startup')
async def get_users():
    users_db = AsyncIOMotorClient('mongodb://localhost:27017').users
    app.users = users_db


@app.post('/sign-up')
async def sign_up(email: str = Form(), password: str = Form()):

    data = {'email': email, 'password': password}
    db_user = await app.users.users.find_one({'email': email})
    if db_user:
        return 'Email taken'
    await app.users.users.insert_one(data)


@app.post('/login')
async def login(email: str = Form(), password: str = Form()):
    db_user = await app.users.users.find_one({'email': email})
    if db_user['password'] == password:
        return 'Logged in'
    return 'Not logged in'


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8001)