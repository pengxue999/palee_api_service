from pydantic import BaseModel, Field
from typing import Optional
from app.enums.gender import GenderEnum

class DormitoryBase(BaseModel):
    gender: GenderEnum
    max_capacity: int

class DormitoryCreate(DormitoryBase):
    pass

class DormitoryUpdate(BaseModel):
    gender: Optional[GenderEnum] = None
    max_capacity: Optional[int] = None

class DormitoryResponse(DormitoryBase):
    dormitory_id: int

    class Config:
        from_attributes = True
