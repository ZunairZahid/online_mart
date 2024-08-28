from datetime import datetime
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from google.protobuf.timestamp_pb2 import Timestamp
from sqlmodel import SQLModel, Session, create_engine
import asyncio
from app import settings
import bcrypt

def datetime_to_timestamp(dt: datetime) -> Timestamp:
    timestamp = Timestamp()
    timestamp.FromDatetime(dt)
    return timestamp

connection_string = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)

engine = create_engine(
    connection_string, connect_args={}, pool_recycle=300
)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

async def consume_messages(topic, bootstrap_servers):
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id="my-group",
        auto_offset_reset='earliest'
    )

    await consumer.start()
    try:
        async for message in consumer:
            print(f"Received message: {message.value.decode()} on topic {message.topic}")
    finally:
        await consumer.stop()

def get_session():
    with Session(engine) as session:
        yield session

async def get_kafka_producer():
    producer = AIOKafkaProducer(bootstrap_servers='broker:19092')
    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
