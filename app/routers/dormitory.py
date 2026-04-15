from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.configs.database import get_db
from app.models.dormitory import Dormitory as DormitoryModel
from app.schemas.dormitory import DormitoryCreate, DormitoryUpdate, DormitoryResponse
from app.configs.response import success_response, error_response
from app.services import dormitory as svc

router = APIRouter(prefix="/dormitories", tags=["dormitories"])

@router.get("")
def get_all_dormitories(db: Session = Depends(get_db)):
    dormitories = svc.get_all(db)
    return success_response(
        [DormitoryResponse.model_validate(dormitory) for dormitory in dormitories],
        "ດຶງຂໍ້ມູນຫ້ອງພັກທັງໝົດສຳເລັດ"
    )

@router.get("/{dormitory_id}")
def get_dormitory(dormitory_id: int, db: Session = Depends(get_db)):
    try:
        dormitory = svc.get_by_id(db, dormitory_id)
        return success_response(
            DormitoryResponse.model_validate(dormitory),
            "ດຶງຂໍ້ມູນຫ້ອງພັກສຳເລັດ"
        )
    except Exception:
        return error_response("NOT_FOUND", "ບໍ່ພົບຂໍ້ມູນຫ້ອງພັກ", 404)

@router.post("")
def create_dormitory(dormitory: DormitoryCreate, db: Session = Depends(get_db)):
    created_dormitory = svc.create(db, dormitory)
    return success_response(
        DormitoryResponse.model_validate(created_dormitory),
        "ບັນທຶກຫ້ອງພັກສຳເລັດ", 201
    )

@router.put("/{dormitory_id}")
def update_dormitory(dormitory_id: int, dormitory: DormitoryUpdate, db: Session = Depends(get_db)):
    try:
        updated_dormitory = svc.update(db, dormitory_id, dormitory)
        return success_response(
            DormitoryResponse.model_validate(updated_dormitory),
            "ອັບເດດຫ້ອງພັກສຳເລັດ"
        )
    except Exception:
        return error_response("NOT_FOUND", "ບໍ່ພົບຂໍ້ມູນຫ້ອງພັກ", 404)

@router.delete("/{dormitory_id}")
def delete_dormitory(dormitory_id: int, db: Session = Depends(get_db)):
    try:
        svc.delete(db, dormitory_id)
        return success_response(None, "ລຶບຫ້ອງພັກສຳເລັດ")
    except Exception:
        return error_response("NOT_FOUND", "ບໍ່ພົບຂໍ້ມູນຫ້ອງພັກ", 404)
