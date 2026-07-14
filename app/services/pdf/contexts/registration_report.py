from datetime import datetime

from app.services.pdf.assets import font_data_urls


def build_registration_report_context(report_data: dict) -> dict:
    regular_font_url, bold_font_url = font_data_urls()
    filters = report_data.get("filters") or {}

    subject_name = filters.get("subject_name") or ""
    level_name = filters.get("level_name") or ""
    total_count = report_data.get("total_count", 0)

    if subject_name and level_name:
        report_title = f"ລາຍຊື່ນັກຮຽນທີ່ລົງທະບຽນຮຽນ ວິຊາ: {subject_name}-{level_name}"
    elif subject_name:
        report_title = f"ລາຍຊື່ນັກຮຽນທີ່ລົງທະບຽນຮຽນ ວິຊາ: {subject_name}"
    elif level_name:
        report_title = f"ລາຍຊື່ນັກຮຽນທີ່ລົງທະບຽນ ລະດັບ: {level_name}"
    else:
        report_title = "ລາຍຊື່ນັກຮຽນທີ່ລົງທະບຽນ"

    return {
        "font_regular_url": regular_font_url,
        "font_bold_url": bold_font_url,
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "report_title": report_title,
        "total_count": total_count,
        "registrations": report_data.get("registrations", []),
    }
