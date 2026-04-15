from sqlalchemy import Column, String, Date, ForeignKey, Enum,CHAR
from sqlalchemy.orm import relationship
from app.configs.database import Base
from app.enums.semester import SemesterEnum


class Evaluation(Base):
    __tablename__ = "evaluation"

    evaluation_id = Column(String(20), primary_key=True)
    academic_id = Column(CHAR(5), ForeignKey("academic_years.academic_id"), nullable=False)
    semester = Column(Enum(SemesterEnum), nullable=False)
    evaluation_date = Column(Date, nullable=False)

    academic_year = relationship("AcademicYear", back_populates="evaluations")
    evaluation_subjects = relationship("EvaluationSubject", back_populates="evaluation")
