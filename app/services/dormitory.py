from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.dormitory import Dormitory
from app.schemas.dormitory import DormitoryCreate, DormitoryUpdate
from app.configs.exceptions import ConflictException, NotFoundException
from app.utils.foreign_key_helper import safe_delete_with_constraint_check


def get_all(db: Session) -> List[Dormitory]:
    return db.query(Dormitory).all()


def get_by_id(db: Session, dormitory_id: int) -> Dormitory:
    obj = db.query(Dormitory).filter(Dormitory.dormitory_id == dormitory_id).first()
    if not obj:
        raise NotFoundException("ຂໍ້ມູນຫໍພັກ")
    return obj


def create(db: Session, data: DormitoryCreate) -> Dormitory:
    existing = db.query(Dormitory).filter(Dormitory.gender == data.gender).first()
    if existing:
        raise ConflictException(f"ຫໍພັກສຳລັບເພດ {data.gender} ມີແລ້ວ")

    obj = Dormitory(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, dormitory_id: int, data: DormitoryUpdate) -> Dormitory:
    obj = get_by_id(db, dormitory_id)
    update_data = data.model_dump(exclude_unset=True)

    if 'gender' in update_data:
        existing = db.query(Dormitory).filter(
            Dormitory.gender == update_data['gender'],
            Dormitory.dormitory_id != dormitory_id
        ).first()
        if existing:
            raise ConflictException(f"ຫໍພັກສຳລັບເພດ {update_data['gender']} ມີແລ້ວ")

    for field, value in update_data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, dormitory_id: int):
    obj = get_by_id(db, dormitory_id)
    safe_delete_with_constraint_check(db, obj, "dormitory")
