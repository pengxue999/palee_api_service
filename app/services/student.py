from sqlalchemy import func
from sqlalchemy.orm import Session
import time
from app.models.student import Student
from app.models.dormitory import Dormitory
from app.schemas.student import StudentCreate, StudentUpdate
from app.configs.exceptions import NotFoundException, ConflictException
from app.utils.foreign_key_helper import safe_delete_with_constraint_check


def _generate_student_id(db: Session) -> str:
    """
    ສ້າງ Student ID ໃຫ້ຕໍ່າກວ່າກັນ ກັບ retry logic ເພື່ອປ້ອງກັນ race condition
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # ໃຊ້ FOR UPDATE lock ເພື່ອ lock ແຖວສຸດທ້າຍ
            last_student = (
                db.query(Student)
                .order_by(
                    func.length(Student.student_id).desc(),
                    Student.student_id.desc()
                )
                .with_for_update()  # 🔒 ລັອກກາກບາດ race condition
                .first()
            )
            if not last_student:
                return "ST001"
            last_id = last_student.student_id
            if last_id.startswith("ST") and last_id[2:].isdigit():
                num = int(last_id[2:]) + 1
                return f"ST{num:03d}"
            return "ST001"
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # exponential backoff
                continue
            raise


def _get_dormitory_by_gender(db: Session, gender: str) -> Dormitory:
    """ດຶງຂໍ້ມູນຫໍພັກຕາມເພດ"""
    dormitory = db.query(Dormitory).filter(Dormitory.gender == gender).first()
    if not dormitory:
        raise NotFoundException(f"ບໍ່ພົບຂໍ້ມູນຫໍພັກສຳລັບ{gender}")
    return dormitory


def _check_dormitory_capacity(db: Session, gender: str) -> int:
    """
    ກວດສອບວ່າຫໍພັກຍັງວ່າງຢູ່ບໍ່
    Returns: dormitory_id ຖ້າວ່າງ, ຖ້າເຕັມ throw ConflictException
    """
    dormitory = _get_dormitory_by_gender(db, gender)

    current_count = db.query(Student).filter(
        Student.dormitory_id == dormitory.dormitory_id
    ).count()

    if current_count >= dormitory.max_capacity:
        raise ConflictException(
            message=f"ຫໍພັກ{gender}ເຕັມແລ້ວ (ຈຳກັດ {dormitory.max_capacity} ຄົນ, ມີນັກຮຽນ {current_count} ຄົນ)"
        )

    return dormitory.dormitory_id


def get_all(db: Session):
    return db.query(Student).all()


def get_by_id(db: Session, student_id: str):
    obj = db.query(Student).filter(Student.student_id == student_id).first()
    if not obj:
        raise NotFoundException("ຂໍ້ມູນນັກຮຽນ")
    return obj


def create(db: Session, data: StudentCreate):
    """
    ສ້າງໂຣຟາຍນັກຮຽນໃໝ່ ກັບ concurrency protection
    - Student ID ຖືກສ້າງຕາມລຳດັບໂດຍ row locking
    - Dormitory capacity ຖືກກວດກາ ແລະ ອັບເດດພາຍໃນ transaction ດຽວ
    """
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            # ກວດສອບ dormitory ຖ້າຕ້ອງການ
            dormitory_id = None
            if data.dormitory_type == "ຫໍພັກໃນ":
                # Lock dormitory row ບໍ່ໃຫ້ໂຕອື່ນດັດແປງພາຍໃນ transaction
                dormitory = db.query(Dormitory).filter(
                    Dormitory.gender == data.gender
                ).with_for_update().first()

                if not dormitory:
                    raise NotFoundException(
                        f"ບໍ່ພົບຂໍ້ມູນຫໍພັກສຳລັບ{data.gender}"
                    )

                current_count = db.query(Student).filter(
                    Student.dormitory_id == dormitory.dormitory_id
                ).count()

                if current_count >= dormitory.max_capacity:
                    raise ConflictException(
                        message=f"ຫໍພັກ{data.gender}ເຕັມແລ້ວ (ຈຳກັດ {dormitory.max_capacity} ຄົນ, ມີນັກຮຽນ {current_count} ຄົນ)"
                    )
                dormitory_id = dormitory.dormitory_id

            # ສ້າງ student ID (ມີລັອກພາຍໃນ transaction)
            student_id = _generate_student_id(db)

            # ສ້າງໂຣຟາຍໃໝ່
            student_data = {
                "student_id": student_id,
                "student_name": data.student_name,
                "student_lastname": data.student_lastname,
                "gender": data.gender,
                "student_contact": data.student_contact,
                "parents_contact": data.parents_contact,
                "school": data.school,
                "district_id": data.district_id,
                "dormitory_id": dormitory_id
            }

            obj = Student(**student_data)
            db.add(obj)
            db.commit()  # atomic commit
            db.refresh(obj)
            return obj

        except ConflictException:
            # ຫໍພັກເຕັມ - ບໍ່ຕ້ອງ retry
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            last_error = e
            if attempt < max_retries - 1:
                # retry ກັບ backoff
                time.sleep(0.1 * (attempt + 1))
                continue
            raise



def update(db: Session, student_id: str, data: StudentUpdate):
    """
    ອັບເດດຂໍ້ມູນນັກຮຽນ ກັບ concurrency protection
    """
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            # Lock ໂຣຟາຍນັກຮຽນ
            obj = db.query(Student).filter(
                Student.student_id == student_id
            ).with_for_update().first()

            if not obj:
                raise NotFoundException("ຂໍ້ມູນນັກຮຽນ")

            current_gender = obj.gender
            current_dormitory_id = obj.dormitory_id

            if data.dormitory_type is not None:
                if data.dormitory_type == "ຫໍພັກໃນ":
                    new_gender = data.gender if data.gender is not None else current_gender

                    # ກວດ dormitory capacity ພາຍໃນ transaction
                    dormitory = db.query(Dormitory).filter(
                        Dormitory.gender == new_gender
                    ).with_for_update().first()

                    if not dormitory:
                        raise NotFoundException(
                            f"ບໍ່ພົບຂໍ້ມູນຫໍພັກສຳລັບ{new_gender}"
                        )

                    if current_dormitory_id is None:
                        current_count = db.query(Student).filter(
                            Student.dormitory_id == dormitory.dormitory_id
                        ).count()

                        if current_count >= dormitory.max_capacity:
                            raise ConflictException(
                                message=f"ຫໍພັກ{new_gender}ເຕັມແລ້ວ"
                            )
                        dormitory_id = dormitory.dormitory_id
                    else:
                        current_dorm = db.query(Dormitory).filter(
                            Dormitory.dormitory_id == current_dormitory_id
                        ).first()

                        if current_dorm and current_dorm.gender != new_gender:
                            current_count = db.query(Student).filter(
                                Student.dormitory_id == dormitory.dormitory_id
                            ).count()

                            if current_count >= dormitory.max_capacity:
                                raise ConflictException(
                                    message=f"ຫໍພັກ{new_gender}ເຕັມແລ້ວ"
                                )
                            dormitory_id = dormitory.dormitory_id
                        else:
                            dormitory_id = current_dormitory_id

                    update_dict = data.model_dump(exclude_none=True)
                    update_dict["dormitory_id"] = dormitory_id
                    del update_dict["dormitory_type"]

                    for field, value in update_dict.items():
                        setattr(obj, field, value)
                else:
                    update_dict = data.model_dump(exclude_none=True)
                    update_dict["dormitory_id"] = None
                    del update_dict["dormitory_type"]

                    for field, value in update_dict.items():
                        setattr(obj, field, value)
            else:
                for field, value in data.model_dump(exclude_none=True).items():
                    if field != "dormitory_type":
                        setattr(obj, field, value)

            db.commit()
            db.refresh(obj)
            return obj

        except ConflictException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
                continue
            raise



def delete(db: Session, student_id: str):
    obj = get_by_id(db, student_id)
    safe_delete_with_constraint_check(db, obj, "student")
