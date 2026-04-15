from sqlalchemy.orm import Session, joinedload
from app.models.income import Income
from app.schemas.income import IncomeCreate, IncomeUpdate
from app.configs.exceptions import NotFoundException


def _query(db: Session):
    return db.query(Income).options(
        joinedload(Income.tuition_payment),
        joinedload(Income.donation),
    )


def get_all(db: Session):
    return _query(db).all()


def get_by_id(db: Session, income_id: int) -> Income:
    obj = _query(db).filter(Income.income_id == income_id).first()
    if not obj:
        raise NotFoundException("ຂໍ້ມູນລາຍຮັບ")
    return obj


def create(db: Session, data: IncomeCreate):
    obj = Income(**data.model_dump())
    db.add(obj)
    db.commit()
    return get_by_id(db, obj.income_id)


def update(db: Session, income_id: int, data: IncomeUpdate):
    obj = get_by_id(db, income_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, income_id: int):
    obj = get_by_id(db, income_id)
    db.delete(obj)
    db.commit()
