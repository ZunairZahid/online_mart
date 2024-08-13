from datetime import datetime
from typing import Annotated
from aiokafka import AIOKafkaProducer
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app import tser_pb2
from app.model import Tser
from app.utils import datetime_to_timestamp, get_kafka_producer, get_session, hash_password

router = APIRouter(
    prefix="/users",
    tags=["user_management"]
)


@router.post("/create_user", response_model=Tser)
async def create_user(user: Tser, session: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]) -> Tser:
    user.password_hash = hash_password(user.password_hash)
    user_proto = tser_pb2.Tser(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        password_hash=user.password_hash,
        created_at=datetime_to_timestamp(datetime.now()),
        updated_at=datetime_to_timestamp(datetime.now())
    )
    await producer.send_and_wait("user", user_proto.SerializeToString())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.get("/userprofiles/", response_model=list[Tser])
def getusers(session: Annotated[Session, Depends(get_session)]):
    todos = session.exec(select(Tser)).all()
    return todos