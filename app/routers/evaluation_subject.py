from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.configs.database import get_db
from app.models.evaluation_subject import EvaluationSubject as EvaluationSubjectModel
from app.schemas.evaluation_subject import EvaluationSubjectCreate, EvaluationSubjectUpdate, EvaluationSubjectResponse
from app.configs.response import success_response, error_response
from app.services import evaluation_subject as svc

router = APIRouter(prefix="/evaluation-subjects", tags=["evaluation-subjects"])

@router.get("")
def get_all_evaluation_subjects(db: Session = Depends(get_db)):
    evaluation_subjects = svc.get_all(db)
    return success_response(
        [EvaluationSubjectResponse.model_validate(evaluation_subject) for evaluation_subject in evaluation_subjects],
        "ດຶງຂໍ້ມູນວິຊາປະເມີນຜົນທັງໝົດສຳເລັດ"
    )

@router.get("/{eval_subject_id}")
def get_evaluation_subject(eval_subject_id: int, db: Session = Depends(get_db)):
    try:
        evaluation_subject = svc.get_by_id(db, eval_subject_id)
        return success_response(
            EvaluationSubjectResponse.model_validate(evaluation_subject),
            "ດຶງຂໍ້ມູນວິຊາປະເມີນຜົນສຳເລັດ"
        )
    except Exception:
        return error_response("NOT_FOUND", "ບໍ່ພົບຂໍ້ມູນວິຊາປະເມີນຜົນ", 404)

@router.post("")
def create_evaluation_subject(evaluation_subject: EvaluationSubjectCreate, db: Session = Depends(get_db)):
    created_evaluation_subject = svc.create(db, evaluation_subject)
    return success_response(
        EvaluationSubjectResponse.model_validate(created_evaluation_subject),
        "ບັນທຶກວິຊາປະເມີນຜົນສຳເລັດ", 201
    )

@router.put("/{eval_subject_id}")
def update_evaluation_subject(eval_subject_id: int, evaluation_subject: EvaluationSubjectUpdate, db: Session = Depends(get_db)):
    try:
        updated_evaluation_subject = svc.update(db, eval_subject_id, evaluation_subject)
        return success_response(
            EvaluationSubjectResponse.model_validate(updated_evaluation_subject),
            "ອັບເດດວິຊາປະເມີນຜົນສຳເລັດ"
        )
    except Exception:
        return error_response("NOT_FOUND", "ບໍ່ພົບຂໍ້ມູນວິຊາປະເມີນຜົນ", 404)

@router.delete("/{eval_subject_id}")
def delete_evaluation_subject(eval_subject_id: int, db: Session = Depends(get_db)):
    try:
        svc.delete(db, eval_subject_id)
        return success_response(None, "ລຶບວິຊາປະເມີນຜົນສຳເລັດ")
    except Exception:
        return error_response("NOT_FOUND", "ບໍ່ພົບຂໍ້ມູນວິຊາປະເມີນຜົນ", 404)
