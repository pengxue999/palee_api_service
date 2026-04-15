from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.configs.database import get_db
from app.configs.response import success_response
from app.services import reports as svc
from typing import Optional

router = APIRouter(prefix="/reports", tags=["ລາຍງານ"])


@router.get("/students")
def get_student_report(
    academic_id: Optional[str] = Query(None, description="ລະຫັດສົກຮຽນ (optional)"),
    province_id: Optional[int] = Query(None, description="ລະຫັດແຂວງ (optional)"),
    district_id: Optional[int] = Query(None, description="ລະຫັດເມືອງ (optional)"),
    scholarship: Optional[str] = Query(None, description="ສະຖານະທຶນ: 'ໄດ້ຮັບທຶນ' ຫຼື 'ບໍ່ໄດ້ຮັບທຶນ' (optional)"),
    dormitory_type: Optional[str] = Query(None, description="ປະເພດຫໍພັກ: 'ຫໍພັກໃນ' ຫຼື 'ຫໍພັກນອກ' (optional)"),
    gender: Optional[str] = Query(None, description="ເພດ: 'ຊາຍ' ຫຼື 'ຍິງ' (optional)"),
    db: Session = Depends(get_db)
):
    """
    ລາຍງານຂໍ້ມູນນັກຮຽນຕາມເງື່ອນໄຂຕ່າງໆ

    - academic_id: ກັ່ນຕອງຕາມສົກຮຽນ
    - province_id: ກັ່ນຕອງຕາມແຂວງ
    - district_id: ກັ່ນຕອງຕາມເມືອງ
    - scholarship: ກັ່ນຕອງຕາມສະຖານະທຶນ
    - dormitory_type: ກັ່ນຕອງຕາມປະເພດຫໍພັກ
    - gender: ກັ່ນຕອງຕາມເພດ
    """
    result = svc.get_student_report(
        db,
        academic_id=academic_id,
        province_id=province_id,
        district_id=district_id,
        scholarship=scholarship,
        dormitory_type=dormitory_type,
        gender=gender
    )
    return success_response(result, "ດຶງຂໍ້ມູນລາຍງານນັກຮຽນສຳເລັດ")


@router.get("/students/export")
def export_student_report(
    academic_id: Optional[str] = Query(None, description="ລະຫັດສົກຮຽນ (optional)"),
    province_id: Optional[int] = Query(None, description="ລະຫັດແຂວງ (optional)"),
    district_id: Optional[int] = Query(None, description="ລະຫັດເມືອງ (optional)"),
    scholarship: Optional[str] = Query(None, description="ສະຖານະທຶນ (optional)"),
    dormitory_type: Optional[str] = Query(None, description="ປະເພດຫໍພັກ (optional)"),
    gender: Optional[str] = Query(None, description="ເພດ (optional)"),
    format: str = Query("csv", description="ຮູບແບບໄຟລ໌: csv ຫຼື excel"),
    db: Session = Depends(get_db)
):
    """
    Export ຂໍ້ມູນນັກຮຽນເປັນ CSV ຫຼື Excel
    """
    result = svc.export_student_report(
        db,
        academic_id=academic_id,
        province_id=province_id,
        district_id=district_id,
        scholarship=scholarship,
        dormitory_type=dormitory_type,
        gender=gender,
        format=format
    )
    return success_response(result, "Export ຂໍ້ມູນສຳເລັດ")


@router.get("/students/summary")
def get_student_summary(
    academic_id: Optional[str] = Query(None, description="ລະຫັດສົກຮຽນ (optional)"),
    db: Session = Depends(get_db)
):
    """
    ສະຫຼຸບຂໍ້ມູນນັກຮຽນຕາມຫົວຂໍ້ຕ່າງໆ

    - ຈຳນວນນັກຮຽນທັງໝົດ
    - ແຍກຕາມເພດ
    - ແຍກຕາມທຶນ
    - ແຍກຕາມຫໍພັກ
    - ແຍກຕາມແຂວງ/ເມືອງ
    """
    result = svc.get_student_summary(db, academic_id=academic_id)
    return success_response(result, "ດຶງຂໍ້ມູນສະຫຼຸບນັກຮຽນສຳເລັດ")


@router.get("/teacher-attendance")
def get_teacher_attendance_report(
    academic_id: Optional[str] = Query(None, description="ລະຫັດສົກຮຽນ (optional)"),
    month: Optional[str] = Query(None, description="ເດືອນ (YYYY-MM) (optional)"),
    status: Optional[str] = Query(None, description="ສະຖານະ: 'ຂຶ້ນສອນ' ຫຼື 'ຂາດສອນ' (optional)"),
    teacher_id: Optional[str] = Query(None, description="ລະຫັດອາຈານ (optional)"),
    db: Session = Depends(get_db)
):
    """
    ລາຍງານຂໍ້ມູນການເຂົ້າສອນຂອງອາຈານ

    - academic_id: ກັ່ນຕອງຕາມສົກຮຽນ
    - month: ກັ່ນຕອງຕາມເດືອນ (YYYY-MM)
    - status: ກັ່ນຕອງຕາມສະຖານະ (ຂຶ້ນສອນ/ຂາດສອນ)
    - teacher_id: ກັ່ນຕອງຕາມອາຈານ
    """
    result = svc.get_teacher_attendance_report(
        db,
        academic_id=academic_id,
        month=month,
        status=status,
        teacher_id=teacher_id
    )
    return success_response(result, "ດຶງຂໍ້ມູນລາຍງານການເຂົ້າສອນສຳເລັດ")


@router.get("/teacher-attendance/export")
def export_teacher_attendance_report(
    academic_id: Optional[str] = Query(None, description="ລະຫັດສົກຮຽນ (optional)"),
    month: Optional[str] = Query(None, description="ເດືອນ (YYYY-MM) (optional)"),
    status: Optional[str] = Query(None, description="ສະຖານະ (optional)"),
    teacher_id: Optional[str] = Query(None, description="ລະຫັດອາຈານ (optional)"),
    format: str = Query("csv", description="ຮູບແບບໄຟລ໌: csv ຫຼື excel"),
    db: Session = Depends(get_db)
):
    """
    Export ຂໍ້ມູນການເຂົ້າສອນຂອງອາຈານເປັນ CSV ຫຼື Excel
    """
    result = svc.export_teacher_attendance_report(
        db,
        academic_id=academic_id,
        month=month,
        status=status,
        teacher_id=teacher_id,
        format=format
    )
    return success_response(result, "Export ຂໍ້ມູນສຳເລັດ")


@router.get("/finance")
def get_finance_report(
    academic_id: Optional[str] = Query(None, description="ລະຫັດສົກຮຽນ (optional)"),
    year: Optional[int] = Query(None, description="ປີ (YYYY) (optional)"),
    db: Session = Depends(get_db)
):
    """
    ລາຍງານຂໍ້ມູນການເງິນ (ລາຍຮັບ, ລາຍຈ່າຍ, ແລະ ຍອດເຫຼືອ)

    - academic_id: ກັ່ນຕອງຕາມສົກຮຽນ
    - year: ກັ່ນຕອງຕາມປີ (ສຳລັບ graph ລາຍຮັບ-ລາຍຈ່າຍ)
    """
    result = svc.get_finance_report(
        db,
        academic_id=academic_id,
        year=year
    )
    return success_response(result, "ດຶງຂໍ້ມູນລາຍງານການເງິນສຳເລັດ")


@router.get("/finance/export")
def export_finance_report(
    academic_id: Optional[str] = Query(None, description="ລະຫັດສົກຮຽນ (optional)"),
    year: Optional[int] = Query(None, description="ປີ (YYYY) (optional)"),
    format: str = Query("csv", description="ຮູບແບບໄຟລ໌: csv ຫຼື excel"),
    db: Session = Depends(get_db)
):
    """
    Export ຂໍ້ມູນລາຍງານການເງິນເປັນ CSV ຫຼື Excel
    """
    result = svc.export_finance_report(
        db,
        academic_id=academic_id,
        year=year,
        format=format
    )
    return success_response(result, "Export ຂໍ້ມູນສຳເລັດ")


@router.get("/popular-subjects")
def get_popular_subjects_report(
    academic_id: Optional[str] = Query(None, description="ລະຫັດສົກຮຽນ (optional)"),
    db: Session = Depends(get_db)
):
    """
    ລາຍງານວິຊາທີ່ນັກຮຽນມັກຮຽນຫຼາຍທີ່ສຸດ (Popular Subjects Report)

    - academic_id: ກັ່ນຕອງຕາມສົກຮຽນ
    - ສະແດງສະຖິຕິວິຊາທີ່ນັກຮຽນລົງທະບຽນຫຼາຍທີ່ສຸດ
    - ລວມທັງ: ຊື່ວິຊາ, ໝວດວິຊາ, ລະດັບ, ຈຳນວນນັກຮຽນ, ເປີເຊັນ
    """
    result = svc.get_popular_subjects_report(
        db,
        academic_id=academic_id
    )
    return success_response(result, "ດຶງຂໍ້ມູນວິຊາຍອດນິຍົມສຳເລັດ")
