from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import date
from decimal import Decimal


def format_date(value):
    """Format date to YYYY-MM-DD string"""
    if value is None:
        return None
    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")
    return value


class EvaluationCreate(BaseModel):
    evaluation_id: str
    semester: str
    evaluation_date: date

class EvaluationUpdate(BaseModel):
    semester: Optional[str] = None
    evaluation_date: Optional[date] = None

class EvaluationResponse(BaseModel):
    evaluation_id: str
    semester: str
    evaluation_date: date
    model_config = {"from_attributes": True}

    @field_serializer('evaluation_date')
    def serialize_evaluation_date(self, value):
        return format_date(value)


class EvaluationDetailCreate(BaseModel):
    evaluation_id: str
    student_id: str
    fee_id: str
    score: Decimal
    ranking: str
    prize: Optional[str] = None

class EvaluationDetailUpdate(BaseModel):
    evaluation_id: Optional[str] = None
    student_id: Optional[str] = None
    fee_id: Optional[str] = None
    score: Optional[Decimal] = None
    ranking: Optional[str] = None
    prize: Optional[str] = None

class EvaluationDetailResponse(BaseModel):
    eval_detail_id: int
    evaluation_id: str
    student_name: str
    student_lastname: str
    subject_name: str
    level_name: str
    score: Decimal
    ranking: str
    prize: Optional[str]

    @classmethod
    def model_validate(cls, obj):
        return cls(
            eval_detail_id=obj.eval_detail_id,
            evaluation_id=obj.evaluation_id,
            student_name=obj.student.student_name,
            student_lastname=obj.student.student_lastname,
            subject_name=obj.fee.subject.subject_name,
            level_name=obj.fee.level.level_name,
            score=obj.score,
            ranking=obj.ranking,
            prize=obj.prize
        )

    model_config = {"from_attributes": True}
