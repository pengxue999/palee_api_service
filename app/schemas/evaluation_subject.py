from pydantic import BaseModel, Field
from typing import Optional

class EvaluationSubjectBase(BaseModel):
    evaluation_id: str = Field(..., max_length=20)
    subject_detail_id: str = Field(..., max_length=5)

class EvaluationSubjectCreate(EvaluationSubjectBase):
    pass

class EvaluationSubjectUpdate(BaseModel):
    evaluation_id: Optional[str] = Field(None, max_length=20)
    subject_detail_id: Optional[str] = Field(None, max_length=5)

class EvaluationSubjectResponse(EvaluationSubjectBase):
    eval_subject_id: int

    class Config:
        from_attributes = True
