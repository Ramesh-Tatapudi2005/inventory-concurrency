from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy import text
import time
import random

from .database import engine, get_db, Base
from .models import Product, Order
from .schemas import OrderCreate, ProductResponse

app = FastAPI()

# Create tables on startup
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database connection failed")

@app.get("/api/products/{id}", response_model=ProductResponse)
def get_product(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/api/orders/pessimistic", status_code=201)
def place_order_pessimistic(data: OrderCreate, db: Session = Depends(get_db)):
    try:
        # Step 3: Acquire row-level lock using FOR UPDATE
        product = db.query(Product).with_for_update().filter(Product.id == data.productId).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if product.stock < data.quantity:
            db.add(Order(product_id=data.productId, quantity_ordered=data.quantity, 
                         user_id=data.userId, status="FAILED_OUT_OF_STOCK"))
            db.commit()
            raise HTTPException(status_code=400, detail="Insufficient stock")

        product.stock -= data.quantity
        new_order = Order(product_id=product.id, quantity_ordered=data.quantity, 
                          user_id=data.userId, status="SUCCESS")
        db.add(new_order)
        db.commit()
        return {
            "orderId": new_order.id, 
            "productId": product.id, 
            "quantityOrdered": data.quantity, 
            "stockRemaining": product.stock
        }
    except Exception as e:
        db.rollback()
        raise e

@app.post("/api/orders/optimistic", status_code=201)
def place_order_optimistic(data: OrderCreate, db: Session = Depends(get_db)):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Step 4: Standard read for version checking
            product = db.query(Product).filter(Product.id == data.productId).first()
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
                
            if product.stock < data.quantity:
                db.add(Order(product_id=data.productId, quantity_ordered=data.quantity, 
                             user_id=data.userId, status="FAILED_OUT_OF_STOCK"))
                db.commit()
                raise HTTPException(status_code=400, detail="Insufficient stock")

            # Update handles versioning automatically via SQLAlchemy mapper
            product.stock -= data.quantity
            new_order = Order(product_id=product.id, quantity_ordered=data.quantity, 
                              user_id=data.userId, status="SUCCESS")
            db.add(new_order)
            db.commit() 
            
            return {
                "orderId": new_order.id, 
                "productId": product.id,
                "quantityOrdered": data.quantity,
                "stockRemaining": product.stock, 
                "newVersion": product.version
            }

        except StaleDataError:
            db.rollback()
            if attempt < max_retries - 1:
                # Exponential backoff: 50ms * 2^attempt
                time.sleep((0.05 * (2 ** attempt)) + (random.uniform(0, 0.01)))
                continue
            
            db.add(Order(product_id=data.productId, quantity_ordered=data.quantity, 
                         user_id=data.userId, status="FAILED_CONFLICT"))
            db.commit()
            raise HTTPException(status_code=409, detail="Failed to place order due to concurrent modification. Please try again.")

@app.get("/api/orders/stats")
def get_stats(db: Session = Depends(get_db)):
    return {
        "totalOrders": db.query(Order).count(),
        "successfulOrders": db.query(Order).filter(Order.status == "SUCCESS").count(),
        "failedOutOfStock": db.query(Order).filter(Order.status == "FAILED_OUT_OF_STOCK").count(),
        "failedConflict": db.query(Order).filter(Order.status == "FAILED_CONFLICT").count()
    }

@app.post("/api/products/reset")
def reset_inventory(db: Session = Depends(get_db)):
    db.query(Order).delete()
    db.query(Product).filter(Product.id == 1).update({"stock": 100, "version": 1})
    db.query(Product).filter(Product.id == 2).update({"stock": 50, "version": 1})
    db.commit()
    return {"message": "Product inventory reset successfully."}