from sqlalchemy.orm import Session
from app.models.evaluation import Evaluation
from app.models.evaluation_detail import EvaluationDetail
from app.schemas.evaluation import (
    EvaluationCreate, EvaluationUpdate,
    EvaluationDetailCreate, EvaluationDetailUpdate,
)


def get_all(db: Session):
    return db.query(Evaluation).all()


def get_by_id(db: Session, evaluation_id: str):
    return db.query(Evaluation).filter(Evaluation.evaluation_id == evaluation_id).first()


def create(db: Session, data: EvaluationCreate):
    obj = Evaluation(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, evaluation_id: str, data: EvaluationUpdate):
    obj = get_by_id(db, evaluation_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, evaluation_id: str) -> bool:
    obj = get_by_id(db, evaluation_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_all_details(db: Session):
    return db.query(EvaluationDetail).all()


def get_detail(db: Session, detail_id: int):
    return db.query(EvaluationDetail).filter(EvaluationDetail.eval_detail_id == detail_id).first()


def create_detail(db: Session, data: EvaluationDetailCreate):
    obj = EvaluationDetail(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_detail(db: Session, detail_id: int, data: EvaluationDetailUpdate):
    obj = get_detail(db, detail_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_detail(db: Session, detail_id: int) -> bool:
    obj = get_detail(db, detail_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
