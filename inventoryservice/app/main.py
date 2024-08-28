from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import asyncio
from app import settings
from app.model import Products
from app.routers import  create_product
from app.utils import (
    create_db_and_tables, 
    consume_messages, 
    get_session, 
    get_kafka_producer, 
    hash_password
)

from app.consumers.product_event_consumer import consume_product_created_events

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(consume_product_created_events())


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables..")
    task = asyncio.create_task(consume_messages('user', 'broker:19092'))
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Mart Inventory API", 
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8002",
            "description": "Development Server"
        }
    ])

@app.get("/")
def read_root():
    return {"Welcome to Zunair's ": "Inventory API Services"}

origins = [
    "http://localhost",
    "http://localhost:8002",
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


app.include_router(create_product.router)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8004, log_level="info")
