from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.configs.database import Base


class EvaluationDetail(Base):
    __tablename__ = "evaluation_detail"

    eval_detail_id = Column(Integer, primary_key=True, autoincrement=True)
    eval_subject_id = Column(Integer, ForeignKey("evaluation_subject.eval_subject_id"), nullable=False)
    student_id = Column(String(10), ForeignKey("student.student_id"), nullable=False)
    score = Column(DECIMAL(5, 2), nullable=False)
    ranking = Column(String(10), nullable=False)
    prize = Column(String(100), nullable=True)

    evaluation_subject = relationship("EvaluationSubject", back_populates="evaluation_details")
    student = relationship("Student", back_populates="evaluation_details")
