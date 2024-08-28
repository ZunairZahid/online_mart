from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional


class Products(SQLModel, table=True):
    product_id: Optional[int] = Field(default=None, primary_key=True)
    description: str = Field(index=True, unique=True, nullable=False)
    unit_of_measure : str = Field(index=True, nullable=False)
    price: float = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False, sa_column_kwargs={"onupdate": datetime.now})
