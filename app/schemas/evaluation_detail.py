from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


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
    student_id: str
    fee_id: str
    score: Decimal
    ranking: str
    prize: Optional[str] = None

    model_config = {"from_attributes": True}
