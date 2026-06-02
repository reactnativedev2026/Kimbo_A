from sqlmodel import SQLModel
from typing import Optional, List
from datetime import datetime

# Product Type Schemas
class ProductTypeBase(SQLModel):
    name: str
    description: Optional[str] = None
    unit: str = "Piece"
    is_active: bool = True

class ProductTypeCreate(ProductTypeBase):
    pass

class ProductTypeUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None

class ProductTypeRead(ProductTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

class ProductTypeResponse(SQLModel):
    status: str
    message: str
    data: ProductTypeRead

class ProductTypeListResponse(SQLModel):
    status: str
    message: str
    data: List[ProductTypeRead]

# Product Schemas
class ProductBase(SQLModel):
    name: str
    description: Optional[str] = None
    product_type_id: int
    unit: Optional[str] = None
    price_per_unit: float
    token_points_per_unit: float
    image_url: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    product_type_id: Optional[int] = None
    unit: Optional[str] = None
    price_per_unit: Optional[float] = None
    token_points_per_unit: Optional[float] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProductRead(ProductBase):
    id: int
    product_type: Optional[ProductTypeRead] = None

    created_at: datetime
    updated_at: datetime

class ProductResponse(SQLModel):
    status: str
    message: str
    data: ProductRead

class ProductListResponse(SQLModel):
    status: str
    message: str
    data: List[ProductRead]

class DeleteResponse(SQLModel):
    status: str
    message: str
    deleted_id: int
