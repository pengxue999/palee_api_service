from pydantic import BaseModel
from typing import Optional


class DonationCategoryCreate(BaseModel):
    donation_category: str


class DonationCategoryUpdate(BaseModel):
    donation_category: Optional[str] = None


class DonationCategoryResponse(BaseModel):
    donation_category_id: int
    donation_category: str

    model_config = {"from_attributes": True}
