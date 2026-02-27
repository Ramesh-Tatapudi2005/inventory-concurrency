from pydantic import BaseModel

class OrderCreate(BaseModel):
    productId: int
    quantity: int
    userId: str

class ProductResponse(BaseModel):
    id: int
    name: str
    stock: int
    version: int

    class Config:
        from_attributes = True