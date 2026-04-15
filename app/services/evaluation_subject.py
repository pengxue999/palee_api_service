from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.evaluation_subject import EvaluationSubject
from app.schemas.evaluation_subject import EvaluationSubjectCreate, EvaluationSubjectUpdate

class EvaluationSubjectService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[EvaluationSubject]:
        return self.db.query(EvaluationSubject).all()

    def get_by_id(self, eval_subject_id: int) -> Optional[EvaluationSubject]:
        return self.db.query(EvaluationSubject).filter(EvaluationSubject.eval_subject_id == eval_subject_id).first()

    def create(self, evaluation_subject_data: EvaluationSubjectCreate) -> EvaluationSubject:
        db_evaluation_subject = EvaluationSubject(**evaluation_subject_data.dict())
        self.db.add(db_evaluation_subject)
        self.db.commit()
        self.db.refresh(db_evaluation_subject)
        return db_evaluation_subject

    def update(self, eval_subject_id: int, evaluation_subject_data: EvaluationSubjectUpdate) -> Optional[EvaluationSubject]:
        db_evaluation_subject = self.get_by_id(eval_subject_id)
        if not db_evaluation_subject:
            return None

        update_data = evaluation_subject_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_evaluation_subject, field, value)

        self.db.commit()
        self.db.refresh(db_evaluation_subject)
        return db_evaluation_subject

    def delete(self, eval_subject_id: int) -> bool:
        db_evaluation_subject = self.get_by_id(eval_subject_id)
        if not db_evaluation_subject:
            return False

        self.db.delete(db_evaluation_subject)
        self.db.commit()
        return True
