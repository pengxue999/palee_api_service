from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.donor import Donor
from app.models.donation_category import DonationCategory
from app.models.donation import Donation
from app.models.income import Income
from app.schemas.donation import (
    DonationCreate, DonationUpdate,
)
from app.configs.exceptions import NotFoundException


def _is_cash_donation(db: Session, category_id: int) -> bool:
    """Check if donation category is 'ເງິນສົດ' (cash donation)"""
    category = db.query(DonationCategory).filter(
        DonationCategory.donation_category_id == category_id
    ).first()
    return category and category.donation_category == "ເງິນສົດ"



def get_all(db: Session):
    return db.query(Donation).options(
        joinedload(Donation.donor),
        joinedload(Donation.donation_category),
        joinedload(Donation.unit)
    ).all()


def get_by_id(db: Session, donation_id: int) -> Donation:
    obj = db.query(Donation).options(
        joinedload(Donation.donor),
        joinedload(Donation.donation_category),
        joinedload(Donation.unit)
    ).filter(Donation.donation_id == donation_id).first()
    if not obj:
        raise NotFoundException("ຂໍ້ມູນການບໍລິຈາກ")
    return obj


def create(db: Session, data: DonationCreate):
    obj = Donation(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)

    if _is_cash_donation(db, data.donation_category_id):
        donor = db.query(Donor).filter(Donor.donor_id == data.donor_id).first()
        donor_fullname = ""
        if donor:
            donor_fullname = f"{donor.donor_name} {donor.donor_lastname}"

        income = Income(
            donation_id=obj.donation_id,
            amount=data.amount,
            description=f"ການບໍລິຈາກ: {donor_fullname}" if donor_fullname else f"ການບໍລິຈາກ: {data.donation_name}",
            income_date=data.donation_date if data.donation_date else func.now(),
        )
        db.add(income)
        db.commit()

    return obj


def update(db: Session, donation_id: int, data: DonationUpdate):
    obj = get_by_id(db, donation_id)
    old_category_id = obj.donation_category_id
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)

    new_category_id = obj.donation_category_id

    if not _is_cash_donation(db, old_category_id) and _is_cash_donation(db, new_category_id):
        donor = db.query(Donor).filter(Donor.donor_id == obj.donor_id).first()
        donor_fullname = ""
        if donor:
            donor_fullname = f"{donor.donor_name} {donor.donor_lastname}"

        income = Income(
            donation_id=obj.donation_id,
            amount=obj.amount,
            description=f"ການບໍລິຈາກ: {donor_fullname}" if donor_fullname else f"ການບໍລິຈາກ: {obj.donation_name}",
            income_date=obj.donation_date if obj.donation_date else func.now(),
        )
        db.add(income)
        db.commit()

    elif _is_cash_donation(db, old_category_id) and not _is_cash_donation(db, new_category_id):
        income = db.query(Income).filter(Income.donation_id == donation_id).first()
        if income:
            db.delete(income)
            db.commit()

    elif _is_cash_donation(db, old_category_id) and _is_cash_donation(db, new_category_id):
        if data.amount is not None or data.donation_date is not None:
            income = db.query(Income).filter(Income.donation_id == donation_id).first()
            if income:
                if data.amount is not None:
                    income.amount = data.amount
                if data.donation_date is not None:
                    income.income_date = data.donation_date
                db.commit()

    return obj


def delete(db: Session, donation_id: int):
    obj = get_by_id(db, donation_id)

    if _is_cash_donation(db, obj.donation_category_id):
        income = db.query(Income).filter(Income.donation_id == donation_id).first()
        if income:
            db.delete(income)

    db.delete(obj)
    db.commit()
