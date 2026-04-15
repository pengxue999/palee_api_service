from sqlalchemy import Column, Integer, String, CHAR, ForeignKey
from sqlalchemy.orm import relationship
from app.configs.database import Base


class EvaluationSubject(Base):
    __tablename__ = "evaluation_subject"

    eval_subject_id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_id = Column(String(20), ForeignKey("evaluation.evaluation_id"), nullable=False)
    subject_detail_id = Column(CHAR(5), ForeignKey("subject_detail.subject_detail_id"), nullable=False)

    evaluation = relationship("Evaluation", back_populates="evaluation_subjects")
    subject_detail = relationship("SubjectDetail", back_populates="evaluation_subjects")
    evaluation_details = relationship("EvaluationDetail", back_populates="evaluation_subject")
