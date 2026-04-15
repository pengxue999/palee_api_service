from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.configs.database import get_db
from app.schemas.tuition_payment import TuitionPaymentCreate, TuitionPaymentUpdate, TuitionPaymentResponse
from app.configs.response import success_response
from app.services import tuition_payment as svc

router = APIRouter(prefix="/tuition-payments", tags=["ການຈ່າຍຄ່າຮຽນ"])


@router.get("")
def get_all(db: Session = Depends(get_db)):
    data = svc.get_all(db)
    return success_response(
        [TuitionPaymentResponse.model_validate(item) for item in data],
        "ດຶງຂໍ້ມູນການຈ່າຍຄ່າຮຽນທັງໝົດສຳເລັດ"
    )


@router.get("/by-registration/{registration_id}")
def get_by_registration(registration_id: str, db: Session = Depends(get_db)):
    data = svc.get_by_registration(db, registration_id)
    return success_response(
        [TuitionPaymentResponse.model_validate(item) for item in data],
        "ດຶງຂໍ້ມູນການຈ່າຍຄ່າຮຽນຕາມລົງທະບຽນສຳເລັດ"
    )


@router.get("/{payment_id}")
def get_one(payment_id: str, db: Session = Depends(get_db)):
    return success_response(
        TuitionPaymentResponse.model_validate(svc.get_by_id(db, payment_id)),
        "ດຶງຂໍ້ມູນການຈ່າຍຄ່າຮຽນສຳເລັດ"
    )


@router.post("")
def create(data: TuitionPaymentCreate, db: Session = Depends(get_db)):
    return success_response(
        TuitionPaymentResponse.model_validate(svc.create(db, data)),
        "ບັນທຶກການຈ່າຍຄ່າຮຽນສຳເລັດ", 201
    )


@router.put("/{payment_id}")
def update(payment_id: str, data: TuitionPaymentUpdate, db: Session = Depends(get_db)):
    return success_response(
        TuitionPaymentResponse.model_validate(svc.update(db, payment_id, data)),
        "ອັບເດດການຈ່າຍຄ່າຮຽນສຳເລັດ"
    )


@router.delete("/{payment_id}")
def delete(payment_id: str, db: Session = Depends(get_db)):
    svc.delete(db, payment_id)
    return success_response(None, "ລຶບການຈ່າຍຄ່າຮຽນສຳເລັດ")
