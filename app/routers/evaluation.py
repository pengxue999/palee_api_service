from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.configs.database import get_db
from app.schemas.evaluation import EvaluationCreate, EvaluationUpdate, EvaluationResponse
from app.configs.response import success_response, error_response
from app.services import evaluation as svc

router = APIRouter(prefix="/evaluations", tags=["ການປະເມີນຜົນ"])


@router.get("")
def get_evaluations(db: Session = Depends(get_db)):
    data = svc.get_all(db)
    return success_response(
        [EvaluationResponse.model_validate(item) for item in data],
        "ດຶງຂໍ້ມູນການປະເມີນຜົນທັງໝົດສຳເລັດ"
    )


@router.get("/{evaluation_id}")
def get_evaluation(evaluation_id: str, db: Session = Depends(get_db)):
    obj = svc.get_by_id(db, evaluation_id)
    if not obj:
        return error_response("NOT_FOUND", "ບໍ່ພົບການປະເມີນຜົນ", 404)
    return success_response(
        EvaluationResponse.model_validate(obj),
        "ດຶງຂໍ້ມູນການປະເມີນຜົນສຳເລັດ"
    )


@router.post("")
def create_evaluation(data: EvaluationCreate, db: Session = Depends(get_db)):
    return success_response(
        EvaluationResponse.model_validate(svc.create(db, data)),
        "ບັນທຶກການປະເມີນຜົນສຳເລັດ", 201
    )


@router.put("/{evaluation_id}")
def update_evaluation(evaluation_id: str, data: EvaluationUpdate, db: Session = Depends(get_db)):
    obj = svc.update(db, evaluation_id, data)
    if not obj:
        return error_response("NOT_FOUND", "ບໍ່ພົບການປະເມີນຜົນ", 404)
    return success_response(
        EvaluationResponse.model_validate(obj),
        "ອັບເດດການປະເມີນຜົນສຳເລັດ"
    )


@router.delete("/{evaluation_id}")
def delete_evaluation(evaluation_id: str, db: Session = Depends(get_db)):
    if not svc.delete(db, evaluation_id):
        return error_response("NOT_FOUND", "ບໍ່ພົບການປະເມີນຜົນ", 404)
    return success_response(None, "ລຶບການປະເມີນຜົນສຳເລັດ")
