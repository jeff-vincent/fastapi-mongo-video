from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.post('/sign-up')
async def sign_up():
    return 'success'

@app.post('/session')
async def session():
    return 'success'


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8001)