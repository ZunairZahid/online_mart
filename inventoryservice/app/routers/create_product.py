from datetime import datetime
from typing import Annotated
from aiokafka import AIOKafkaProducer
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, update, delete
from app import product_pb2
from app.model import Products
from app.utils import datetime_to_timestamp, get_kafka_producer, get_session, hash_password

router = APIRouter(
    prefix="/products",
    tags=["product_admin"]
)


@router.post("/create_product", response_model=Products)
async def create_product(new_product: Products,
                         session: Annotated[Session, Depends(get_session)],
                         producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]) -> Products:
    
    # Create Protobuf message
    product_proto = product_pb2.Product(
        product_id=new_product.product_id,
        description=new_product.description,
        unit_of_measure=new_product.unit_of_measure,
        price=new_product.price,
        created_at=datetime_to_timestamp(datetime.now()),
        updated_at=datetime_to_timestamp(datetime.now())
    )

    # Send Kafka message
    await producer.send_and_wait("productCreated", product_proto.SerializeToString())

    # Add the new product to the database
    session.add(new_product)
    session.commit()
    session.refresh(new_product)
    
    return new_product

@router.get("/product_list/", response_model=list[Products])
def getproducts(session: Annotated[Session, Depends(get_session)]):
    getallproducts = session.exec(select(Products)).all()
    return getallproducts

@router.get("/product/{prod_id}", response_model=Products)
def get_product(prod_id: int, session: Annotated[Session, Depends(get_session)]):
    getsingleproduct = session.exec(select(Products).where(Products.product_id == prod_id)).one_or_none()
    if not getsingleproduct:
        raise HTTPException(status_code=404, detail="No product found")
    return getsingleproduct


@router.put("/update_product/{prod_id}", response_model=Products)
async def update_product(prod_id: int, price: float, 
                         session: Annotated[Session, Depends(get_session)],
                         producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
    try:
        # Query to find the product
        sql = select(Products).where(Products.product_id == prod_id)
        product = session.exec(sql).one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="No product found")
        
        # Update the product with the new price and updated_at timestamp
        update_query = (
            update(Products)
            .where(Products.product_id == prod_id)
            .values(price=price, updated_at=datetime.now())
        )
        session.exec(update_query)
        session.commit()

        # Refresh the product object to get the updated values
        session.refresh(product)

        # Create Protobuf message
        product_proto = product_pb2.Product(
            product_id=product.product_id,
            description=product.description,
            unit_of_measure=product.unit_of_measure,
            price=product.price,
            created_at=datetime_to_timestamp(product.created_at),
            updated_at=datetime_to_timestamp(datetime.now())
        )
        
        # Send Kafka message
        await producer.send_and_wait("productUpdated", product_proto.SerializeToString())

        return product  
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Some error occurred: {str(e)}")

@router.delete("/delete_product/{prod_id}", response_model=dict)
async def del_product(prod_id: int, session: Annotated[Session, Depends(get_session)],
                      producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
    try:
        # Query to find the product
        sql = select(Products).where(Products.product_id == prod_id)
        product = session.exec(sql).one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="No Product Found")
        
        # Delete the product
        del_query = delete(Products).where(Products.product_id == prod_id)
        session.exec(del_query)
        session.commit()

        # Create Protobuf message
        product_proto = product_pb2.Product(
            product_id=product.product_id,
            description=product.description,
            unit_of_measure=product.unit_of_measure,
            price=product.price,
            created_at=datetime_to_timestamp(product.created_at),
            updated_at=datetime_to_timestamp(datetime.now())
        )
        
        # Send Kafka message
        await producer.send_and_wait("productDeleted", product_proto.SerializeToString())
        
        return {"message": "Product deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Some error occurred: {str(e)}")
