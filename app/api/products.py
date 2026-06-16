from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import and_, func
from typing import List
from app.database import engine, get_session
from app.models import ProductType, Product, User
from app.schemas.product_schema import (
    ProductTypeCreate, ProductTypeUpdate, ProductTypeResponse, ProductTypeListResponse, ProductTypeRead,
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, ProductRead, DeleteResponse
)
from app.api.users import get_current_admin, get_current_contractor, get_current_user

router = APIRouter()

# ==============================
# PRODUCT TYPES
# ==============================

@router.post("/types", response_model=ProductTypeResponse)
def add_product_type(
    type_data: ProductTypeCreate,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    existing_type = session.exec(select(ProductType).where(ProductType.name == type_data.name)).first()
    if existing_type:
        raise HTTPException(status_code=400, detail="Product type already exists")

    db_type = ProductType.model_validate(type_data)
    session.add(db_type)
    session.commit()
    session.refresh(db_type)

    return {
        "status": "success",
        "message": "Product type added successfully",
        "data": db_type
    }

@router.get("/types", response_model=ProductTypeListResponse)
def get_product_types(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # Anyone can view active types
):
    # Query active product types and count active products per type.
    type_counts = {
        row[0]: row[1]
        for row in session.exec(
            select(ProductType.id, func.count(Product.id))
            .join(
                Product,
                and_(Product.product_type_id == ProductType.id, Product.is_active == True),
                isouter=True,
            )
            .where(ProductType.is_active == True)
            .group_by(ProductType.id)
        ).all()
    }

    types = session.exec(select(ProductType).where(ProductType.is_active == True).order_by(ProductType.created_at.desc())).all()
    type_reads = []
    for t in types:
        values = t.model_dump() if hasattr(t, 'model_dump') else t.__dict__
        values['product_count'] = type_counts.get(t.id, 0)
        type_reads.append(ProductTypeRead.model_validate(values) if hasattr(ProductTypeRead, 'model_validate') else ProductTypeRead(**values))

    return {
        "status": "success",
        "message": "Product types fetched",
        "data": type_reads
    }

@router.patch("/types/{type_id}", response_model=ProductTypeResponse)
def update_product_type(
    type_id: int,
    type_data: ProductTypeUpdate,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    db_type = session.get(ProductType, type_id)
    if not db_type:
        raise HTTPException(status_code=404, detail="Product type not found")
        
    update_data = type_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_type, key, value)
        
    session.add(db_type)
    session.commit()
    session.refresh(db_type)
    
    return {
        "status": "success",
        "message": "Product type updated successfully",
        "data": db_type
    }

@router.delete("/types/{type_id}", response_model=DeleteResponse)
def delete_product_type(
    type_id: int,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    db_type = session.get(ProductType, type_id)
    if not db_type:
        raise HTTPException(status_code=404, detail="Product type not found")
        
    db_type.is_active = False
    session.add(db_type)
    session.commit()
    
    return {
        "status": "success",
        "message": "Product type deleted successfully",
        "deleted_id": type_id
    }

# ==============================
# PRODUCTS
# ==============================

@router.post("/", response_model=ProductResponse)
def add_product(
    product_data: ProductCreate,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    # Check if product type exists
    p_type = session.get(ProductType, product_data.product_type_id)
    if not p_type:
        raise HTTPException(status_code=404, detail="Product type not found")

    db_product = Product.model_validate(product_data)
    # Assign the unit from the category (ProductType)
    db_product.unit = p_type.unit
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)

    db_product.product_type = p_type

    return {
        "status": "success",
        "message": "Product added successfully",
        "data": db_product
    }

@router.get("/", response_model=ProductListResponse)
def get_products(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # Anyone can view products
):
    products = session.exec(select(Product).where(Product.is_active == True).order_by(Product.created_at.desc())).all()
    product_reads = [ProductRead.model_validate(p) if hasattr(ProductRead, 'model_validate') else ProductRead.from_orm(p) for p in products]
    return {
        "status": "success",
        "message": "Products fetched",
        "data": product_reads
    }

@router.get("/by-type/{type_id}", response_model=ProductListResponse)
def get_products_by_type(
    type_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    products = session.exec(select(Product).where(Product.product_type_id == type_id, Product.is_active == True).order_by(Product.created_at.desc())).all()
    product_reads = [ProductRead.model_validate(p) if hasattr(ProductRead, 'model_validate') else ProductRead.from_orm(p) for p in products]
    return {
        "status": "success",
        "message": f"Products for type {type_id} fetched",
        "data": product_reads
    }

@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    update_data = product_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    # Re-sync unit from the product type (category)
    p_type = session.get(ProductType, db_product.product_type_id)
    if p_type:
        db_product.unit = p_type.unit
        
    session.add(db_product)
    session.commit()
    session.refresh(db_product)

    db_product.product_type = p_type
    
    return {
        "status": "success",
        "message": "Product updated successfully",
        "data": db_product
    }

@router.delete("/{product_id}", response_model=DeleteResponse)
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_product.is_active = False
    session.add(db_product)
    session.commit()
    
    return {
        "status": "success",
        "message": "Product deleted successfully",
        "deleted_id": product_id
    }
