from typing import Any, Dict, Optional

from openpyxl import Workbook
from sqlalchemy.orm import Session, joinedload

from app.enums.registration_status import RegistrationStatusEnum
from app.models.academic_years import AcademicYear
from app.models.district import District
from app.models.fee import Fee
from app.models.level import Level
from app.models.province import Province
from app.models.registration import Registration
from app.models.registration_detail import RegistrationDetail
from app.models.subject import Subject
from app.models.subject_detail import SubjectDetail
from app.services.reporting.common import (
    apply_excel_title,
    create_excel_theme,
    current_timestamp,
    finalize_workbook_export,
    set_excel_column_widths,
    write_excel_table_headers,
    write_excel_table_rows,
)


def get_registration_report(
    db: Session,
    status: Optional[str] = None,
    subject_id: Optional[str] = None,
    level_id: Optional[str] = None,
) -> Dict[str, Any]:
    # Pre-load lookup maps once to avoid N+1 queries
    academic_year_map: Dict[str, str] = {
        ay.academic_id: ay.academic_year
        for ay in db.query(AcademicYear).all()
    }
    district_map: Dict[int, tuple] = {
        d.district_id: (d.district_name, d.province_id)
        for d in db.query(District).all()
    }
    province_map: Dict[int, str] = {
        p.province_id: p.province_name
        for p in db.query(Province).all()
    }

    query = db.query(Registration).options(
        joinedload(Registration.student),
        joinedload(Registration.details)
        .joinedload(RegistrationDetail.fee_rel)
        .joinedload(Fee.subject_detail)
        .joinedload(SubjectDetail.subject),
        joinedload(Registration.details)
        .joinedload(RegistrationDetail.fee_rel)
        .joinedload(Fee.subject_detail)
        .joinedload(SubjectDetail.level),
    )

    if status:
        if status == "PAID_OR_PARTIAL":
            query = query.filter(
                Registration.status.in_([
                    RegistrationStatusEnum.PAID,
                    RegistrationStatusEnum.PARTIAL,
                ])
            )
        else:
            status_map = {
                RegistrationStatusEnum.PAID.value: RegistrationStatusEnum.PAID,
                RegistrationStatusEnum.UNPAID.value: RegistrationStatusEnum.UNPAID,
                RegistrationStatusEnum.PARTIAL.value: RegistrationStatusEnum.PARTIAL,
            }
            status_enum = status_map.get(status)
            if status_enum:
                query = query.filter(Registration.status == status_enum)

    if subject_id or level_id:
        query = (
            query.join(
                RegistrationDetail,
                Registration.registration_id == RegistrationDetail.registration_id,
            )
            .join(Fee, RegistrationDetail.fee_id == Fee.fee_id)
            .join(SubjectDetail, Fee.subject_detail_id == SubjectDetail.subject_detail_id)
        )
        if subject_id:
            query = query.filter(SubjectDetail.subject_id == subject_id)
        if level_id:
            query = query.filter(SubjectDetail.level_id == level_id)
        query = query.distinct()

    registrations = query.order_by(Registration.registration_date.desc()).all()

    # Resolve subject/level names for filter display
    subject_name = None
    if subject_id:
        subj = db.query(Subject).filter(Subject.subject_id == subject_id).first()
        if subj:
            subject_name = subj.subject_name

    level_name = None
    if level_id:
        lvl = db.query(Level).filter(Level.level_id == level_id).first()
        if lvl:
            level_name = lvl.level_name

    registration_list = []
    for reg in registrations:
        student = reg.student
        academic_year_name = None
        if reg.details:
            for detail in reg.details:
                if detail.fee_rel and detail.fee_rel.academic_id:
                    academic_year_name = academic_year_map.get(detail.fee_rel.academic_id)
                    if academic_year_name:
                        break

        district_name = None
        province_name = None
        if student and student.district_id:
            dist = district_map.get(student.district_id)
            if dist:
                district_name = dist[0]
                province_name = province_map.get(dist[1])

        registration_list.append(
            {
                "registration_id": reg.registration_id,
                "student_id": student.student_id if student else None,
                "full_name": (
                    f"{student.student_name} {student.student_lastname}"
                    if student else None
                ),
                "gender": student.gender if student else None,
                "school": student.school if student else None,
                "district_name": district_name,
                "province_name": province_name,
                "academic_year_name": academic_year_name,
                "status": reg.status.value if reg.status else None,
                "registration_date": (
                    reg.registration_date.strftime("%Y-%m-%d %H:%M:%S")
                    if reg.registration_date else None
                ),
            }
        )

    paid_count = sum(1 for r in registration_list if r["status"] == RegistrationStatusEnum.PAID.value)
    unpaid_count = sum(1 for r in registration_list if r["status"] == RegistrationStatusEnum.UNPAID.value)
    partial_count = sum(1 for r in registration_list if r["status"] == RegistrationStatusEnum.PARTIAL.value)

    return {
        "filters": {
            "status": status,
            "subject_id": subject_id,
            "subject_name": subject_name,
            "level_id": level_id,
            "level_name": level_name,
        },
        "total_count": len(registration_list),
        "paid_count": paid_count,
        "unpaid_count": unpaid_count,
        "partial_count": partial_count,
        "registrations": registration_list,
    }


def export_registration_report(
    db: Session,
    status: Optional[str] = None,
    subject_id: Optional[str] = None,
    level_id: Optional[str] = None,
) -> Dict[str, Any]:
    report_data = get_registration_report(
        db, status=status, subject_id=subject_id, level_id=level_id
    )
    registrations = report_data["registrations"]

    # Excel only — columns: student_id, full_name, gender, school, district, province
    headers = [
        "ລະຫັດນັກຮຽນ",
        "ຊື່-ນາມສະກຸນ",
        "ເພດ",
        "ໂຮງຮຽນ",
        "ເມືອງ",
        "ແຂວງ",
    ]

    subject_name = report_data["filters"].get("subject_name") or ""
    level_name = report_data["filters"].get("level_name") or ""
    total_count = report_data["total_count"]

    parts = [p for p in [subject_name, level_name] if p]
    title = " ".join(parts) + f" ({total_count} ຄົນ)" if parts else f"ລາຍງານການລົງທະບຽນ ({total_count} ຄົນ)"

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Registrations"
    theme = create_excel_theme()

    apply_excel_title(
        sheet,
        title=title,
        from_column=1,
        to_column=len(headers),
        theme=theme,
    )

    header_row = 2
    write_excel_table_headers(sheet, headers=headers, row_index=header_row, theme=theme)
    write_excel_table_rows(
        sheet,
        rows=[
            [
                reg["student_id"] or "-",
                reg["full_name"] or "-",
                reg["gender"] or "-",
                reg["school"] or "-",
                reg["district_name"] or "-",
                reg["province_name"] or "-",
            ]
            for reg in registrations
        ],
        start_row=header_row + 1,
        theme=theme,
    )

    sheet.freeze_panes = f"A{header_row + 1}"
    sheet.auto_filter.ref = (
        f"A{header_row}:F{max(header_row, header_row + len(registrations))}"
    )
    set_excel_column_widths(
        sheet,
        {1: 14, 2: 24, 3: 10, 4: 28, 5: 18, 6: 18},
    )

    filters_desc = []
    if subject_name:
        filters_desc.append(subject_name)
    if level_name:
        filters_desc.append(level_name)
    filter_str = "_".join(filters_desc) if filters_desc else "ທັງໝົດ"

    filename = f"ລາຍຊື່ນັກຮຽນ_{filter_str}.xlsx"
    return finalize_workbook_export(workbook, filename=filename, total_records=len(registrations))
