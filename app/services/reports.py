from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, extract
from typing import Optional, List, Dict, Any
import csv
import io
from datetime import datetime

from app.models.student import Student
from app.models.registration import Registration
from app.models.registration_detail import RegistrationDetail
from app.models.fee import Fee
from app.models.academic_years import AcademicYear
from app.models.district import District
from app.models.province import Province
from app.models.dormitory import Dormitory
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment
from app.models.teaching_log import TeachingLog
from app.models.subject_detail import SubjectDetail
from app.models.subject import Subject
from app.models.level import Level
from app.models.subject_category import SubjectCategory
from app.models.income import Income
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.enums.scholarship import ScholarshipEnum


def get_student_report(
    db: Session,
    academic_id: Optional[str] = None,
    province_id: Optional[int] = None,
    district_id: Optional[int] = None,
    scholarship: Optional[str] = None,
    dormitory_type: Optional[str] = None,
    gender: Optional[str] = None
) -> Dict[str, Any]:
    """
    ລາຍງານຂໍ້ມູນນັກຮຽນຕາມເງື່ອນໄຂຕ່າງໆ
    """
    query = db.query(Student).options(
        joinedload(Student.district).joinedload(District.province),
        joinedload(Student.dormitory)
    )

    applied_filters = {}

    if gender:
        query = query.filter(Student.gender == gender)
        applied_filters['gender'] = gender

    if district_id:
        query = query.filter(Student.district_id == district_id)
        applied_filters['district_id'] = district_id
    elif province_id:
        query = query.join(District).filter(District.province_id == province_id)
        applied_filters['province_id'] = province_id

    if dormitory_type:
        if dormitory_type == "ຫໍພັກໃນ":
            query = query.filter(Student.dormitory_id.isnot(None))
        elif dormitory_type == "ຫໍພັກນອກ":
            query = query.filter(Student.dormitory_id.is_(None))
        applied_filters['dormitory_type'] = dormitory_type

    if academic_id or scholarship:
        query = query.join(
            Registration, Student.student_id == Registration.student_id
        ).join(
            RegistrationDetail, Registration.registration_id == RegistrationDetail.registration_id
        ).join(
            Fee, RegistrationDetail.fee_id == Fee.fee_id
        )

        if academic_id:
            query = query.filter(Fee.academic_id == academic_id)
            applied_filters['academic_id'] = academic_id

        if scholarship:
            scholarship_enum = ScholarshipEnum.RECEIVED if scholarship == "ໄດ້ຮັບທຶນ" else ScholarshipEnum.NOT_RECEIVED
            query = query.filter(RegistrationDetail.scholarship == scholarship_enum)
            applied_filters['scholarship'] = scholarship

        query = query.distinct()

    students = query.all()

    student_list = []
    for student in students:
        student_scholarship = None
        if academic_id:
            reg_detail = db.query(RegistrationDetail).join(
                Registration, RegistrationDetail.registration_id == Registration.registration_id
            ).join(
                Fee, RegistrationDetail.fee_id == Fee.fee_id
            ).filter(
                Registration.student_id == student.student_id,
                Fee.academic_id == academic_id
            ).first()
            if reg_detail:
                student_scholarship = reg_detail.scholarship.value

        student_list.append({
            "student_id": student.student_id,
            "student_name": student.student_name,
            "student_lastname": student.student_lastname,
            "full_name": f"{student.student_name} {student.student_lastname}",
            "gender": student.gender,
            "student_contact": student.student_contact,
            "parents_contact": student.parents_contact,
            "school": student.school,
            "district_name": student.district.district_name if student.district else None,
            "province_name": student.district.province.province_name if student.district and student.district.province else None,
            "dormitory_type": "ຫໍພັກໃນ" if student.dormitory_id else "ຫໍພັກນອກ",
            "scholarship_status": student_scholarship
        })

    academic_year_name = None
    if academic_id:
        academic = db.query(AcademicYear).filter(AcademicYear.academic_id == academic_id).first()
        if academic:
            academic_year_name = academic.academic_year

    province_name = None
    if province_id:
        province = db.query(Province).filter(Province.province_id == province_id).first()
        if province:
            province_name = province.province_name

    district_name = None
    if district_id:
        district = db.query(District).filter(District.district_id == district_id).first()
        if district:
            district_name = district.district_name

    return {
        "filters": {
            "academic_id": academic_id,
            "academic_year_name": academic_year_name,
            "province_id": province_id,
            "province_name": province_name,
            "district_id": district_id,
            "district_name": district_name,
            "scholarship": scholarship,
            "dormitory_type": dormitory_type,
            "gender": gender
        },
        "total_count": len(student_list),
        "students": student_list
    }


def export_student_report(
    db: Session,
    academic_id: Optional[str] = None,
    province_id: Optional[int] = None,
    district_id: Optional[int] = None,
    scholarship: Optional[str] = None,
    dormitory_type: Optional[str] = None,
    gender: Optional[str] = None,
    format: str = "csv"
) -> Dict[str, Any]:
    """
    Export ຂໍ້ມູນນັກຮຽນເປັນ CSV
    """
    report_data = get_student_report(
        db,
        academic_id=academic_id,
        province_id=province_id,
        district_id=district_id,
        scholarship=scholarship,
        dormitory_type=dormitory_type,
        gender=gender
    )

    students = report_data["students"]

    output = io.StringIO()
    writer = csv.writer(output)

    output.write('\ufeff')

    headers = [
        "ລະຫັດນັກຮຽນ",
        "ຊື່",
        "ນາມສະກຸນ",
        "ເພດ",
        "ເບີຕິດຕໍ່",
        "ເບີຜູ້ປົກຄອງ",
        "ໂຮງຮຽນ",
        "ແຂວງ",
        "ເມືອງ",
        "ຫໍພັກ"
    ]
    writer.writerow(headers)

    for student in students:
        writer.writerow([
            student["student_id"],
            student["student_name"],
            student["student_lastname"],
            student["gender"],
            student["student_contact"],
            student["parents_contact"],
            student["school"],
            student["province_name"] or "",
            student["district_name"] or "",
            student["dormitory_type"]
        ])

    csv_content = output.getvalue()
    output.close()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filters_desc = []
    if academic_id:
        filters_desc.append(f"academic_{academic_id}")
    if province_id:
        filters_desc.append(f"province_{province_id}")
    if scholarship:
        filters_desc.append(f"scholarship_{scholarship}")
    if dormitory_type:
        filters_desc.append(f"dorm_{dormitory_type}")

    filter_str = "_".join(filters_desc) if filters_desc else "all"
    filename = f"student_report_{filter_str}_{timestamp}.csv"

    return {
        "filename": filename,
        "content_type": "text/csv; charset=utf-8-sig",
        "data": csv_content,
        "total_records": len(students)
    }


def get_student_summary(db: Session, academic_id: Optional[str] = None) -> Dict[str, Any]:
    """
    ສະຫຼຸບຂໍ້ມູນນັກຮຽນຕາມຫົວຂໍ້ຕ່າງໆ
    """
    base_query = db.query(Student)

    if academic_id:
        base_query = base_query.join(
            Registration, Student.student_id == Registration.student_id
        ).join(
            RegistrationDetail, Registration.registration_id == RegistrationDetail.registration_id
        ).join(
            Fee, RegistrationDetail.fee_id == Fee.fee_id
        ).filter(
            Fee.academic_id == academic_id
        ).distinct()

    total_students = base_query.count()

    gender_stats = {}
    for g in ["ຊາຍ", "ຍິງ"]:
        count = base_query.filter(Student.gender == g).count()
        gender_stats[g] = count

    dormitory_stats = {
        "ຫໍພັກໃນ": base_query.filter(Student.dormitory_id.isnot(None)).count(),
        "ຫໍພັກນອກ": base_query.filter(Student.dormitory_id.is_(None)).count()
    }

    scholarship_stats = {}
    if academic_id:
        for sch in [ScholarshipEnum.RECEIVED, ScholarshipEnum.NOT_RECEIVED]:
            count = db.query(Student).join(
                Registration, Student.student_id == Registration.student_id
            ).join(
                RegistrationDetail, Registration.registration_id == RegistrationDetail.registration_id
            ).join(
                Fee, RegistrationDetail.fee_id == Fee.fee_id
            ).filter(
                Fee.academic_id == academic_id,
                RegistrationDetail.scholarship == sch
            ).distinct().count()
            scholarship_stats[sch.value] = count
    else:
        scholarship_stats = {"ໄດ້ຮັບທຶນ": 0, "ບໍ່ໄດ້ຮັບທຶນ": 0}

    province_stats = {}
    provinces = db.query(Province).all()
    for province in provinces:
        count = base_query.join(District).filter(District.province_id == province.province_id).count()
        if count > 0:
            province_stats[province.province_name] = count

    district_stats = {}
    districts = db.query(District).all()
    for district in districts:
        count = base_query.filter(Student.district_id == district.district_id).count()
        if count > 0:
            district_stats[district.district_name] = count

    district_stats = dict(sorted(district_stats.items(), key=lambda x: x[1], reverse=True)[:10])

    return {
        "total_students": total_students,
        "by_gender": gender_stats,
        "by_dormitory": dormitory_stats,
        "by_scholarship": scholarship_stats,
        "by_province": province_stats,
        "by_district": district_stats
    }


def get_teacher_attendance_report(
    db: Session,
    academic_id: Optional[str] = None,
    month: Optional[str] = None,
    status: Optional[str] = None,
    teacher_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    ລາຍງານຂໍ້ມູນການເຂົ້າສອນຂອງອາຈານ
    """
    query = db.query(TeachingLog).options(
        joinedload(TeachingLog.assignment).joinedload(TeacherAssignment.teacher),
        joinedload(TeachingLog.assignment).joinedload(TeacherAssignment.subject_detail).joinedload(SubjectDetail.subject),
        joinedload(TeachingLog.assignment).joinedload(TeacherAssignment.subject_detail).joinedload(SubjectDetail.level),
        joinedload(TeachingLog.assignment).joinedload(TeacherAssignment.academic_year),
        joinedload(TeachingLog.substitute_assignment).joinedload(TeacherAssignment.teacher),
        joinedload(TeachingLog.substitute_assignment).joinedload(TeacherAssignment.subject_detail).joinedload(SubjectDetail.subject)
    )

    needs_assignment_join = academic_id is not None or teacher_id is not None

    if needs_assignment_join:
        query = query.join(
            TeacherAssignment,
            TeachingLog.assignment_id == TeacherAssignment.assignment_id
        )

        if academic_id:
            query = query.filter(TeacherAssignment.academic_id == academic_id)

        if teacher_id:
            query = query.filter(TeacherAssignment.teacher_id == teacher_id)

    if status:
        query = query.filter(TeachingLog.status == status)

    if month:
        year, mon = month.split('-')
        query = query.filter(
            func.extract('year', TeachingLog.teaching_date) == int(year),
            func.extract('month', TeachingLog.teaching_date) == int(mon)
        )

    logs = query.order_by(TeachingLog.teaching_date.desc()).all()

    log_list = []
    for log in logs:
        assignment = log.assignment
        teacher = assignment.teacher if assignment else None
        subject_detail = assignment.subject_detail if assignment else None
        level = subject_detail.level if subject_detail else None
        academic_year = assignment.academic_year if assignment else None

        is_substitute = log.substitute_for_assignment_id is not None
        substitute_teacher = None
        substitute_subject = None

        if is_substitute and log.substitute_assignment:
            substitute_teacher = log.substitute_assignment.teacher
            substitute_subject = log.substitute_assignment.subject_detail

        hourly = float(log.hourly) if log.hourly else 0
        hourly_rate = float(assignment.hourly_rate) if assignment and assignment.hourly_rate else 0
        total_amount = hourly * hourly_rate

        log_list.append({
            "teaching_log_id": log.teaching_log_id,
            "teacher_id": teacher.teacher_id if teacher else None,
            "teacher_name": teacher.teacher_name if teacher else None,
            "teacher_lastname": teacher.teacher_lastname if teacher else None,
            "full_name": f"{teacher.teacher_name} {teacher.teacher_lastname}" if teacher else None,
            "subject_name": subject_detail.subject.subject_name if subject_detail and subject_detail.subject else None,
            "level_name": level.level_name if level else None,
            "academic_year": academic_year.academic_year if academic_year else None,
            "teaching_date": log.teaching_date.strftime("%Y-%m-%d") if log.teaching_date else None,
            "status": log.status,
            "hourly": hourly,
            "hourly_rate": hourly_rate,
            "total_amount": total_amount,
            "remark": log.remark,
            "is_substitute": is_substitute,
            "substitute_for_teacher_name": substitute_teacher.teacher_name if substitute_teacher else None,
            "substitute_for_teacher_lastname": substitute_teacher.teacher_lastname if substitute_teacher else None,
            "substitute_for_subject_name": substitute_subject.subject.subject_name if substitute_subject and substitute_subject.subject else None
        })

    return {
        "filters": {
            "academic_id": academic_id,
            "month": month,
            "status": status,
            "teacher_id": teacher_id
        },
        "total_count": len(log_list),
        "logs": log_list
    }


def export_teacher_attendance_report(
    db: Session,
    academic_id: Optional[str] = None,
    month: Optional[str] = None,
    status: Optional[str] = None,
    teacher_id: Optional[str] = None,
    format: str = "csv"
) -> Dict[str, Any]:
    """
    Export ຂໍ້ມູນການເຂົ້າສອນຂອງອາຈານເປັນ CSV
    """
    report_data = get_teacher_attendance_report(
        db,
        academic_id=academic_id,
        month=month,
        status=status,
        teacher_id=teacher_id
    )

    logs = report_data["logs"]

    output = io.StringIO()
    writer = csv.writer(output)

    output.write('\ufeff')

    headers = [
        "ອາຈານ",
        "ວິຊາ",
        "ລະດັບ",
        "ສົກຮຽນ",
        "ວັນທີສອນ",
        "ສະຖານະ",
        "ຊົ່ວໂມງ",
        "ຄ່າສອນ/ຊມ",
        "ຈຳນວນເງິນ",
        "ໝາຍເຫດ",
        "ອາຈານທີ່ໃຫ້ສອນແທນ",
        "ວິຊາທີ່ໃຫ້ສອນແທນ"
    ]
    writer.writerow(headers)

    for log in logs:
        writer.writerow([
            log["full_name"] or "",
            log["subject_name"] or (log["substitute_for_subject_name"] or ""),
            log["level_name"] or "",
            log["academic_year"] or "",
            log["teaching_date"] or "",
            log["status"] or "",
            log["hourly"],
            log["hourly_rate"],
            log["total_amount"],
            log["remark"] or "",
            f"{log['substitute_for_teacher_name'] or ''} {log['substitute_for_teacher_lastname'] or ''}".strip() if log["substitute_for_teacher_name"] else "",
            log["substitute_for_subject_name"] or ""
        ])

    csv_content = output.getvalue()
    output.close()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filters_desc = []
    if academic_id:
        filters_desc.append(f"academic_{academic_id}")
    if month:
        filters_desc.append(f"month_{month}")
    if status:
        filters_desc.append(f"status_{status}")
    if teacher_id:
        filters_desc.append(f"teacher_{teacher_id}")

    filter_str = "_".join(filters_desc) if filters_desc else "all"
    filename = f"teacher_attendance_report_{filter_str}_{timestamp}.csv"

    return {
        "filename": filename,
        "content_type": "text/csv; charset=utf-8-sig",
        "data": csv_content,
        "total_records": len(logs)
    }


def get_finance_report(
    db: Session,
    academic_id: Optional[str] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    ລາຍງານຂໍ້ມູນການເງິນ (ລາຍຮັບ, ລາຍຈ່າຍ, ແລະ ຍອດເຫຼືອ)
    """
    income_query = db.query(Income)
    expense_query = db.query(Expense).join(ExpenseCategory)

    if year:
        income_query = income_query.filter(
            extract('year', Income.income_date) == year
        )
        expense_query = expense_query.filter(
            extract('year', Expense.expense_date) == year
        )

    incomes = income_query.all()
    expenses = expense_query.all()

    total_income = sum(float(inc.amount) for inc in incomes)
    total_expense = sum(float(exp.amount) for exp in expenses)
    balance = total_income - total_expense

    tuition_income = sum(float(inc.amount) for inc in incomes if inc.tuition_payment_id is not None)
    donation_income = sum(float(inc.amount) for inc in incomes if inc.donation_id is not None)
    other_income = total_income - tuition_income - donation_income

    income_breakdown = []
    if total_income > 0:
        income_breakdown = [
            {"category": "ຄ່າຮຽນ", "amount": tuition_income, "percentage": round(tuition_income / total_income * 100, 2)},
            {"category": "ການບໍລິຈາກ", "amount": donation_income, "percentage": round(donation_income / total_income * 100, 2)},
            {"category": "ອື່ນໆ", "amount": other_income, "percentage": round(other_income / total_income * 100, 2)}
        ]

    expense_categories = db.query(ExpenseCategory).all()
    expense_breakdown = []
    for category in expense_categories:
        category_expense = sum(
            float(exp.amount) for exp in expenses
            if exp.expense_category_id == category.expense_category_id
        )
        if category_expense > 0:
            percentage = round(category_expense / total_expense * 100, 2) if total_expense > 0 else 0
            expense_breakdown.append({
                "category": category.expense_category,
                "amount": category_expense,
                "percentage": percentage
            })

    expense_breakdown.sort(key=lambda x: x["amount"], reverse=True)

    min_income_year = db.query(func.min(extract('year', Income.income_date))).scalar()
    max_income_year = db.query(func.max(extract('year', Income.income_date))).scalar()
    min_expense_year = db.query(func.min(extract('year', Expense.expense_date))).scalar()
    max_expense_year = db.query(func.max(extract('year', Expense.expense_date))).scalar()

    years_with_data = []
    if min_income_year is not None:
        years_with_data.append(int(min_income_year))
    if max_income_year is not None:
        years_with_data.append(int(max_income_year))
    if min_expense_year is not None:
        years_with_data.append(int(min_expense_year))
    if max_expense_year is not None:
        years_with_data.append(int(max_expense_year))

    if years_with_data:
        start_year = min(years_with_data)
        end_year = max(years_with_data)
    else:
        current_year = datetime.now().year
        start_year = current_year
        end_year = current_year

    yearly_data = []
    for y in range(start_year, end_year + 1):
        year_income = db.query(func.sum(Income.amount)).filter(
            extract('year', Income.income_date) == y
        ).scalar() or 0

        year_expense = db.query(func.sum(Expense.amount)).filter(
            extract('year', Expense.expense_date) == y
        ).scalar() or 0

        yearly_data.append({
            "year": y,
            "income": float(year_income),
            "expense": float(year_expense),
            "balance": float(year_income) - float(year_expense)
        })

    income_list = []
    for inc in incomes:
        income_list.append({
            "income_id": inc.income_id,
            "amount": float(inc.amount),
            "description": inc.description,
            "income_date": inc.income_date.strftime("%Y-%m-%d") if inc.income_date else None,
            "source": "ຄ່າຮຽນ" if inc.tuition_payment_id else ("ການບໍລິຈາກ" if inc.donation_id else "ອື່ນໆ")
        })

    expense_list = []
    for exp in expenses:
        expense_list.append({
            "expense_id": exp.expense_id,
            "amount": float(exp.amount),
            "description": exp.description,
            "expense_date": exp.expense_date.strftime("%Y-%m-%d") if exp.expense_date else None,
            "category": exp.category.expense_category if exp.category else "-"
        })

    academic_year_name = None
    if academic_id:
        academic = db.query(AcademicYear).filter(AcademicYear.academic_id == academic_id).first()
        if academic:
            academic_year_name = academic.academic_year

    return {
        "filters": {
            "academic_id": academic_id,
            "academic_year_name": academic_year_name,
            "year": year
        },
        "summary": {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance
        },
        "income_breakdown": income_breakdown,
        "expense_breakdown": expense_breakdown,
        "yearly_comparison": yearly_data,
        "incomes": income_list,
        "expenses": expense_list,
        "total_income_count": len(income_list),
        "total_expense_count": len(expense_list)
    }


def export_finance_report(
    db: Session,
    academic_id: Optional[str] = None,
    year: Optional[int] = None,
    format: str = "csv"
) -> Dict[str, Any]:
    """
    Export ຂໍ້ມູນລາຍງານການເງິນເປັນ CSV
    """
    report_data = get_finance_report(
        db,
        academic_id=academic_id,
        year=year
    )

    incomes = report_data["incomes"]
    expenses = report_data["expenses"]

    output = io.StringIO()
    writer = csv.writer(output)

    output.write('\ufeff')

    writer.writerow(["ສະຫຼຸບການເງິນ"])
    writer.writerow(["ລາຍຮັບທັງໝົດ", report_data["summary"]["total_income"]])
    writer.writerow(["ລາຍຈ່າຍທັງໝົດ", report_data["summary"]["total_expense"]])
    writer.writerow(["ຍອດເຫຼືອ", report_data["summary"]["balance"]])
    writer.writerow([])

    writer.writerow(["ລາຍຮັບແຍກຕາມແຫຼ່ງ"])
    writer.writerow(["ແຫຼ່ງລາຍຮັບ", "ຈຳນວນເງິນ", "ເປີເຊັນ"])
    for item in report_data["income_breakdown"]:
        writer.writerow([item["category"], item["amount"], f"{item['percentage']}%"])
    writer.writerow([])

    writer.writerow(["ລາຍຈ່າຍແຍກຕາມປະເພດ"])
    writer.writerow(["ປະເພດລາຍຈ່າຍ", "ຈຳນວນເງິນ", "ເປີເຊັນ"])
    for item in report_data["expense_breakdown"]:
        writer.writerow([item["category"], item["amount"], f"{item['percentage']}%"])
    writer.writerow([])

    writer.writerow(["ລາຍລະອຽດລາຍຮັບ"])
    writer.writerow(["ລະຫັດ", "ຈຳນວນເງິນ", "ລາຍລະອຽດ", "ວັນທີ", "ແຫຼ່ງທີ່ມາ"])
    for inc in incomes:
        writer.writerow([
            inc["income_id"],
            inc["amount"],
            inc["description"] or "",
            inc["income_date"] or "",
            inc["source"]
        ])
    writer.writerow([])

    writer.writerow(["ລາຍລະອຽດລາຍຈ່າຍ"])
    writer.writerow(["ລະຫັດ", "ຈຳນວນເງິນ", "ລາຍລະອຽດ", "ວັນທີ", "ປະເພດ"])
    for exp in expenses:
        writer.writerow([
            exp["expense_id"],
            exp["amount"],
            exp["description"] or "",
            exp["expense_date"] or "",
            exp["category"]
        ])

    csv_content = output.getvalue()
    output.close()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filters_desc = []
    if academic_id:
        filters_desc.append(f"academic_{academic_id}")
    if year:
        filters_desc.append(f"year_{year}")

    filter_str = "_".join(filters_desc) if filters_desc else "all"
    filename = f"finance_report_{filter_str}_{timestamp}.csv"

    return {
        "filename": filename,
        "content_type": "text/csv; charset=utf-8-sig",
        "data": csv_content,
        "total_records": len(incomes) + len(expenses)
    }


def get_popular_subjects_report(db: Session, academic_id: Optional[str] = None) -> Dict[str, Any]:
    """
    ລາຍງານວິຊາທີ່ນັກຮຽນມັກຮຽນຫຼາຍທີ່ສຸດ (Popular Subjects Report)
    """
    query = db.query(
        Subject.subject_name,
        SubjectCategory.subject_category_name,
        Level.level_name,
        func.count(RegistrationDetail.registration_id).label('student_count'),
        func.count(func.distinct(RegistrationDetail.registration_id)).label('unique_students'),
        Fee.fee.label('fee_amount')
    ).select_from(
        RegistrationDetail
    ).join(
        Registration, RegistrationDetail.registration_id == Registration.registration_id
    ).join(
        Fee, RegistrationDetail.fee_id == Fee.fee_id
    ).join(
        SubjectDetail, Fee.subject_detail_id == SubjectDetail.subject_detail_id
    ).join(
        Subject, SubjectDetail.subject_id == Subject.subject_id
    ).join(
        SubjectCategory, Subject.subject_category_id == SubjectCategory.subject_category_id
    ).join(
        Level, SubjectDetail.level_id == Level.level_id
    )

    if academic_id:
        query = query.filter(Fee.academic_id == academic_id)

    subject_stats = query.group_by(
        Subject.subject_name,
        SubjectCategory.subject_category_name
    ).with_entities(
        Subject.subject_name,
        SubjectCategory.subject_category_name.label('subject_category'),
        func.count(func.distinct(RegistrationDetail.registration_id)).label('student_count'),
        func.count(SubjectDetail.level_id).label('level_count'),
        func.avg(Fee.fee).label('avg_fee')
    ).all()

    level_stats = query.group_by(
        Subject.subject_name,
        SubjectCategory.subject_category_name,
        Level.level_name,
        Fee.fee
    ).with_entities(
        Subject.subject_name,
        SubjectCategory.subject_category_name.label('subject_category'),
        Level.level_name,
        func.count(func.distinct(RegistrationDetail.registration_id)).label('student_count'),
        Fee.fee.label('fee_amount')
    ).all()

    total_students = db.query(RegistrationDetail).join(
        Fee, RegistrationDetail.fee_id == Fee.fee_id
    ).filter(
        Fee.academic_id == academic_id if academic_id else True
    ).distinct(RegistrationDetail.registration_id).count()

    subjects_data = []
    for stat in subject_stats:
        percentage = (stat.student_count / total_students * 100) if total_students > 0 else 0
        subjects_data.append({
            "subject_name": stat.subject_name,
            "subject_category": stat.subject_category,
            "student_count": stat.student_count,
            "level_count": stat.level_count,
            "avg_fee": float(stat.avg_fee) if stat.avg_fee else 0,
            "percentage": round(percentage, 2)
        })

    subjects_data.sort(key=lambda x: x["student_count"], reverse=True)

    level_data = []
    for stat in level_stats:
        level_data.append({
            "subject_name": stat.subject_name,
            "subject_category": stat.subject_category,
            "level_name": stat.level_name,
            "student_count": stat.student_count,
            "fee_amount": float(stat.fee_amount) if stat.fee_amount else 0
        })

    level_data.sort(key=lambda x: (x["subject_name"], x["level_name"]))

    category_stats = {}
    for subject in subjects_data:
        category = subject["subject_category"]
        if category not in category_stats:
            category_stats[category] = 0
        category_stats[category] += subject["student_count"]

    academic_year_name = None
    if academic_id:
        academic = db.query(AcademicYear).filter(AcademicYear.academic_id == academic_id).first()
        if academic:
            academic_year_name = academic.academic_year

    return {
        "filters": {
            "academic_id": academic_id,
            "academic_year_name": academic_year_name
        },
        "summary": {
            "total_students": total_students,
            "total_subjects": len(subjects_data),
            "total_categories": len(category_stats)
        },
        "subjects": subjects_data,
        "levels": level_data,
        "categories": category_stats
    }
