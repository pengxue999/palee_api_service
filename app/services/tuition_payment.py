from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.tuition_payment import TuitionPayment
from app.models.registration import Registration
from app.models.income import Income
from app.models.student import Student
from app.schemas.tuition_payment import TuitionPaymentCreate, TuitionPaymentUpdate
from app.configs.exceptions import NotFoundException
from app.enums.registration_status import RegistrationStatusEnum
import re


def generate_payment_id(db: Session) -> str:
    """Generate sequential payment ID in format TP0001, TP0002, etc."""
    latest = db.query(TuitionPayment).order_by(
        func.length(TuitionPayment.tuition_payment_id).desc(),
        TuitionPayment.tuition_payment_id.desc()
    ).first()

    if latest and latest.tuition_payment_id:
        match = re.match(r'TP(\d+)', latest.tuition_payment_id)
        if match:
            next_num = int(match.group(1)) + 1
        else:
            next_num = 1
    else:
        next_num = 1

    return f'TP{next_num:04d}'


def _update_registration_status(db: Session, registration_id: str):
    """Recalculate and update registration status based on total paid amount."""
    registration = db.query(Registration).filter(
        Registration.registration_id == registration_id
    ).first()
    if not registration:
        return

    total_paid = db.query(func.sum(TuitionPayment.paid_amount)).filter(
        TuitionPayment.registration_id == registration_id
    ).scalar() or 0

    final_amount = float(registration.final_amount)
    total_paid = float(total_paid)

    if total_paid == 0:
        new_status = RegistrationStatusEnum.UNPAID
    elif total_paid >= final_amount:
        new_status = RegistrationStatusEnum.PAID
    else:
        new_status = RegistrationStatusEnum.PARTIAL

    registration.status = new_status
    db.commit()
    db.refresh(registration)  # Refresh to ensure in-memory object is up-to-date


def get_all(db: Session):
    return db.query(TuitionPayment).options(
        joinedload(TuitionPayment.registration).joinedload(Registration.student)
    ).order_by(TuitionPayment.pay_date.desc()).all()


def get_by_registration(db: Session, registration_id: str):
    return db.query(TuitionPayment).options(
        joinedload(TuitionPayment.registration).joinedload(Registration.student)
    ).filter(TuitionPayment.registration_id == registration_id).order_by(TuitionPayment.pay_date.desc()).all()


def get_by_id(db: Session, tuition_payment_id: str) -> TuitionPayment:
    obj = db.query(TuitionPayment).options(
        joinedload(TuitionPayment.registration).joinedload(Registration.student)
    ).filter(TuitionPayment.tuition_payment_id == tuition_payment_id).first()
    if not obj:
        raise NotFoundException("ຂໍ້ມູນການຈ່າຍຄ່າຮຽນ")
    return obj


def create(db: Session, data: TuitionPaymentCreate):
    tuition_payment_id = generate_payment_id(db)
    obj = TuitionPayment(
        tuition_payment_id=tuition_payment_id,
        **data.model_dump(exclude_none=True)
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _update_registration_status(db, data.registration_id)
    registration = db.query(Registration).options(
        joinedload(Registration.student)
    ).filter(Registration.registration_id == data.registration_id).first()
    student_fullname = ""
    if registration and registration.student:
        student_fullname = f"{registration.student.student_name} {registration.student.student_lastname}"
    income = Income(
        tuition_payment_id=tuition_payment_id,
        amount=data.paid_amount,
        description=f"ຄ່າຮຽນ: {student_fullname}" if student_fullname else f"ຄ່າຮຽນ: {tuition_payment_id}",
        income_date=data.pay_date if data.pay_date else func.now(),
    )
    db.add(income)
    db.commit()
    # Refresh the payment object to ensure it has latest data including updated registration
    db.refresh(obj)
    return get_by_id(db, tuition_payment_id)


def update(db: Session, tuition_payment_id: str, data: TuitionPaymentUpdate):
    obj = get_by_id(db, tuition_payment_id)
    registration_id = obj.registration_id
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    _update_registration_status(db, registration_id)
    if data.paid_amount is not None:
        income = db.query(Income).filter(
            Income.tuition_payment_id == tuition_payment_id
        ).first()
        if income:
            income.amount = data.paid_amount
            if data.pay_date:
                income.income_date = data.pay_date
            db.commit()
    # Refresh to get updated registration status
    db.refresh(obj)
    return obj


def delete(db: Session, tuition_payment_id: str):
    obj = db.query(TuitionPayment).filter(
        TuitionPayment.tuition_payment_id == tuition_payment_id
    ).first()
    if not obj:
        raise NotFoundException("ຂໍ້ມູນການຈ່າຍຄ່າຮຽນ")
    registration_id = obj.registration_id
    db.delete(obj)
    db.commit()
    db.expire_all()
    _update_registration_status(db, registration_id)
