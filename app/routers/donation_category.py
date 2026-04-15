from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.configs.database import get_db
from app.schemas.donation_category import DonationCategoryCreate, DonationCategoryUpdate, DonationCategoryResponse
from app.configs.response import success_response
from app.services import donation_category as svc

router = APIRouter(prefix="/donation-categories", tags=["ປະເພດການບໍລິຈາກ"])


@router.get("")
def get_all(db: Session = Depends(get_db)):
    data = svc.get_all(db)
    return success_response(
        [DonationCategoryResponse.model_validate(item) for item in data],
        "ດຶງຂໍ້ມູນປະເພດການບໍລິຈາກທັງໝົດສຳເລັດ"
    )


@router.get("/{donation_category_id}")
def get_one(donation_category_id: int, db: Session = Depends(get_db)):
    return success_response(
        DonationCategoryResponse.model_validate(svc.get_by_id(db, donation_category_id)),
        "ດຶງຂໍ້ມູນປະເພດການບໍລິຈາກສຳເລັດ"
    )


@router.post("")
def create(data: DonationCategoryCreate, db: Session = Depends(get_db)):
    return success_response(
        DonationCategoryResponse.model_validate(svc.create(db, data)),
        "ບັນທຶກປະເພດການບໍລິຈາກສຳເລັດ", 201
    )


@router.put("/{donation_category_id}")
def update(donation_category_id: int, data: DonationCategoryUpdate, db: Session = Depends(get_db)):
    return success_response(
        DonationCategoryResponse.model_validate(svc.update(db, donation_category_id, data)),
        "ອັບເດດປະເພດການບໍລິຈາກສຳເລັດ"
    )


@router.delete("/{donation_category_id}")
def delete(donation_category_id: int, db: Session = Depends(get_db)):
    svc.delete(db, donation_category_id)
    return success_response(None, "ລຶບປະເພດການບໍລິຈາກສຳເລັດ")
