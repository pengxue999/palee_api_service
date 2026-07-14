from typing import Any, Dict, Optional

from openpyxl import Workbook
from sqlalchemy.orm import Session, joinedload

from app.enums.scholarship import ScholarshipEnum
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
    create_csv_writer,
    create_excel_theme,
    finalize_csv_export,
    finalize_workbook_export,
    set_excel_column_widths,
    write_excel_table_headers,
    write_excel_table_rows,
)


def _normalize_scholarship(scholarship: Optional[str]) -> Optional[ScholarshipEnum]:
    if not scholarship:
        return None
    for member in ScholarshipEnum:
        if scholarship == member.value or scholarship == member.name:
            return member
    return None


def get_scholarship_report(
    db: Session,
    scholarship: Optional[str] = None,
    subject_id: Optional[str] = None,
    level_id: Optional[str] = None,
) -> Dict[str, Any]:
    """ລາຍງານນັກຮຽນທຶນ — ໜຶ່ງແຖວ = ໜຶ່ງວິຊາທີ່ນັກຮຽນລົງທະບຽນ ພ້ອມສະຖານະທຶນ"""
    # Default to "received scholarship" so the report is meaningful out of the box.
    scholarship_enum = _normalize_scholarship(scholarship) or ScholarshipEnum.RECEIVED

    district_map: Dict[int, tuple] = {
        d.district_id: (d.district_name, d.province_id)
        for d in db.query(District).all()
    }
    province_map: Dict[int, str] = {
        p.province_id: p.province_name for p in db.query(Province).all()
    }

    query = (
        db.query(RegistrationDetail)
        .options(
            joinedload(RegistrationDetail.registration).joinedload(
                Registration.student
            ),
            joinedload(RegistrationDetail.fee_rel)
            .joinedload(Fee.subject_detail)
            .joinedload(SubjectDetail.subject),
            joinedload(RegistrationDetail.fee_rel)
            .joinedload(Fee.subject_detail)
            .joinedload(SubjectDetail.level),
        )
        .filter(RegistrationDetail.scholarship == scholarship_enum)
    )

    if subject_id or level_id:
        query = (
            query.join(Fee, RegistrationDetail.fee_id == Fee.fee_id)
            .join(
                SubjectDetail,
                Fee.subject_detail_id == SubjectDetail.subject_detail_id,
            )
        )
        if subject_id:
            query = query.filter(SubjectDetail.subject_id == subject_id)
        if level_id:
            query = query.filter(SubjectDetail.level_id == level_id)

    details = query.all()

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

    items = []
    for detail in details:
        registration = detail.registration
        student = registration.student if registration else None

        subj_name = None
        lvl_name = None
        fee = detail.fee_rel
        if fee and fee.subject_detail:
            if fee.subject_detail.subject:
                subj_name = fee.subject_detail.subject.subject_name
            if fee.subject_detail.level:
                lvl_name = fee.subject_detail.level.level_name

        scholarship_subject = None
        if subj_name and lvl_name:
            scholarship_subject = f"{subj_name}-{lvl_name}"
        elif subj_name:
            scholarship_subject = subj_name

        district_name = None
        province_name = None
        if student and student.district_id:
            dist = district_map.get(student.district_id)
            if dist:
                district_name = dist[0]
                province_name = province_map.get(dist[1])

        items.append(
            {
                "registration_id": detail.registration_id,
                "student_id": student.student_id if student else None,
                "full_name": (
                    f"{student.student_name} {student.student_lastname}"
                    if student
                    else None
                ),
                "gender": student.gender if student else None,
                "scholarship_subject": scholarship_subject,
                "subject_name": subj_name,
                "level_name": lvl_name,
                "student_contact": student.student_contact if student else None,
                "school": student.school if student else None,
                "district_name": district_name,
                "province_name": province_name,
                "scholarship": detail.scholarship.value if detail.scholarship else None,
            }
        )

    items.sort(key=lambda r: (r["full_name"] or "", r["scholarship_subject"] or ""))

    return {
        "filters": {
            "scholarship": scholarship_enum.value,
            "subject_id": subject_id,
            "subject_name": subject_name,
            "level_id": level_id,
            "level_name": level_name,
        },
        "total_count": len(items),
        "students": items,
    }


def export_scholarship_report(
    db: Session,
    scholarship: Optional[str] = None,
    subject_id: Optional[str] = None,
    level_id: Optional[str] = None,
    format: str = "excel",
) -> Dict[str, Any]:
    report_data = get_scholarship_report(
        db, scholarship=scholarship, subject_id=subject_id, level_id=level_id
    )
    students = report_data["students"]
    normalized_format = format.lower()

    headers = [
        "ຊື່-ນາມສະກຸນ",
        "ເພດ",
        "ວິຊາທີ່ໄດ້ຮັບທຶນ",
        "ເບີຕິດຕໍ່",
        "ໂຮງຮຽນ",
        "ເມືອງ",
        "ແຂວງ",
    ]

    scholarship_label = report_data["filters"].get("scholarship") or ""
    subject_name = report_data["filters"].get("subject_name") or ""
    level_name = report_data["filters"].get("level_name") or ""
    total_count = report_data["total_count"]

    def _row(student):
        return [
            student["full_name"] or "-",
            student["gender"] or "-",
            student["scholarship_subject"] or "-",
            student["student_contact"] or "-",
            student["school"] or "-",
            student["district_name"] or "-",
            student["province_name"] or "-",
        ]

    filters_desc = [p for p in [scholarship_label, subject_name, level_name] if p]
    filter_str = "_".join(filters_desc) if filters_desc else "ທັງໝົດ"

    if normalized_format == "csv":
        output, writer = create_csv_writer()
        writer.writerow(headers)
        for student in students:
            writer.writerow(_row(student))
        filename = f"ລາຍງານນັກຮຽນທຶນ_{filter_str}.csv"
        return finalize_csv_export(
            output, filename=filename, total_records=len(students)
        )

    parts = [p for p in [scholarship_label, subject_name, level_name] if p]
    title = (
        ("ລາຍງານນັກຮຽນທຶນ — " + " ".join(parts) if parts else "ລາຍງານນັກຮຽນທຶນ")
        + f" ({total_count} ຄົນ)"
    )

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Scholarship"
    theme = create_excel_theme()

    apply_excel_title(
        sheet,
        title=title,
        from_column=1,
        to_column=len(headers),
        theme=theme,
    )

    header_row = 2
    write_excel_table_headers(
        sheet, headers=headers, row_index=header_row, theme=theme
    )
    write_excel_table_rows(
        sheet,
        rows=[_row(student) for student in students],
        start_row=header_row + 1,
        theme=theme,
    )

    sheet.freeze_panes = f"A{header_row + 1}"
    sheet.auto_filter.ref = (
        f"A{header_row}:G{max(header_row, header_row + len(students))}"
    )
    set_excel_column_widths(
        sheet,
        {1: 24, 2: 10, 3: 22, 4: 16, 5: 28, 6: 18, 7: 18},
    )

    filename = f"ລາຍງານນັກຮຽນທຶນ_{filter_str}.xlsx"
    return finalize_workbook_export(
        workbook, filename=filename, total_records=len(students)
    )
