from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from app.enums.payment_method import PaymentMethodEnum


def format_date(value):
    """Format datetime to DD-MM-YYYY HH:MM:SS string"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")
    return value


class TuitionPaymentCreate(BaseModel):
    registration_id: str
    paid_amount: Decimal
    payment_method: PaymentMethodEnum
    pay_date: Optional[datetime] = None

class TuitionPaymentUpdate(BaseModel):
    registration_id: Optional[str] = None
    paid_amount: Optional[Decimal] = None
    payment_method: Optional[PaymentMethodEnum] = None
    pay_date: Optional[datetime] = None

class TuitionPaymentResponse(BaseModel):
    tuition_payment_id: str
    registration_id: str
    student_name: str
    student_lastname: str
    paid_amount: Decimal
    payment_method: str
    pay_date: datetime

    @classmethod
    def model_validate(cls, obj):
        payment_method = obj.payment_method
        if hasattr(payment_method, 'value'):
            payment_method = payment_method.value
        return cls(
            tuition_payment_id=obj.tuition_payment_id,
            registration_id=obj.registration_id,
            student_name=obj.registration.student.student_name,
            student_lastname=obj.registration.student.student_lastname,
            paid_amount=obj.paid_amount,
            payment_method=payment_method,
            pay_date=obj.pay_date,
        )

    model_config = {"from_attributes": True}

    @field_serializer('pay_date')
    def serialize_pay_date(self, value):
        return format_date(value)
