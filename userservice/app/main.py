from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import asyncio
from app import settings
from app.model import Tser
from app.routers import  create_user, signin
from app.utils import (
    create_db_and_tables, 
    consume_messages, 
    get_session, 
    get_kafka_producer, 
    hash_password
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables..")
    task = asyncio.create_task(consume_messages('user', 'broker:19092'))
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Mart API Services", 
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8000",
            "description": "Development Server"
        }
    ])

@app.get("/")
def read_root():
    return {"Welcome to Zunair's ": "online Mart"}

origins = [
    "http://localhost",
    "http://localhost:8000",
    "https://2013-58-65-161-70.ngrok-free.app",
    # Add more allowed origins here if necessary
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(create_user.router)

app.include_router(signin.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
