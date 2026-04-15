from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.configs.database import Base


class Dormitory(Base):
    __tablename__ = "dormitory"

    dormitory_id = Column(Integer, primary_key=True, autoincrement=True)
    gender = Column(Enum('ຊາຍ', 'ຍິງ', name='genderenum'), nullable=False, unique=True)
    max_capacity = Column(Integer, nullable=False)

    students = relationship("Student", back_populates="dormitory")
