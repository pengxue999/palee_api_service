from sqlalchemy.orm import Session, joinedload
from app.models.evaluation_detail import EvaluationDetail
from app.models.fee import Fee
from app.schemas.evaluation_detail import EvaluationDetailCreate, EvaluationDetailUpdate
from app.configs.exceptions import NotFoundException


def get_all(db: Session):
    return db.query(EvaluationDetail).options(
        joinedload(EvaluationDetail.student),
        joinedload(EvaluationDetail.fee).joinedload(Fee.subject),
        joinedload(EvaluationDetail.fee).joinedload(Fee.level)
    ).all()


def get_by_id(db: Session, eval_detail_id: int):
    obj = db.query(EvaluationDetail).options(
        joinedload(EvaluationDetail.student),
        joinedload(EvaluationDetail.fee).joinedload(Fee.subject),
        joinedload(EvaluationDetail.fee).joinedload(Fee.level)
    ).filter(EvaluationDetail.eval_detail_id == eval_detail_id).first()
    if not obj:
        raise NotFoundException("Evaluation Detail")
    return obj


def create(db: Session, data: EvaluationDetailCreate):
    obj = EvaluationDetail(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, eval_detail_id: int, data: EvaluationDetailUpdate):
    obj = get_by_id(db, eval_detail_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, eval_detail_id: int):
    obj = get_by_id(db, eval_detail_id)
    db.delete(obj)
    db.commit()
