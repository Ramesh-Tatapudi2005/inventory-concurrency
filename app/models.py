from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from datetime import datetime
from .database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    stock = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False, default=1)

    # SQLAlchemy automatic version tracking for Optimistic Locking
    __mapper_args__ = {"version_id_col": version}
    __table_args__ = (CheckConstraint("stock >= 0", name="check_stock_positive"),)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity_ordered = Column(Integer, nullable=False)
    user_id = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False) # SUCCESS, FAILED_OUT_OF_STOCK, FAILED_CONFLICT
    created_at = Column(DateTime, default=datetime.utcnow)