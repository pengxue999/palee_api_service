from app.schemas.tuition_payment import TuitionPaymentReceiptRequest
from app.services.pdf.assets import font_data_urls
from app.services.pdf.formatters import format_currency, format_date


def _other_fee_items(amount):
    if amount == 300000:
        return [
            {
                "label": "ຄ່າວິຊາບັງຄັບ(ຄະນີດຄິດໄວ):",
                "amount": format_currency(300000),
            }
        ]
    if amount == 500000:
        return [
            {
                "label": "ຄ່າວິຊາບັງຄັບ(ຄະນີດຄິດໄວ):",
                "amount": format_currency(300000),
            },
            {
                "label": "ຄ່າຫໍພັກໃນ(ຄ່ານ້ຳ,ຄ່າໄຟ):",
                "amount": format_currency(200000),
            },
        ]
    return []


def build_tuition_payment_context(
    data: TuitionPaymentReceiptRequest,
) -> dict[str, object]:
    regular_font_url, bold_font_url = font_data_urls()
    is_fully_paid = data.remaining_amount <= 0
    other_fee_items = _other_fee_items(data.other_fee_amount)
    return {
        "font_regular_url": regular_font_url,
        "font_bold_url": bold_font_url,
        "tuition_payment_id": data.tuition_payment_id,
        "invoice_id": data.invoice_id,
        "registration_id": data.registration_id,
        "student_name": data.student_name,
        "payment_method": data.payment_method,
        "pay_date": format_date(data.pay_date),
        "installment_label": str(data.installment_index),
        "selected_fees": [
            {
                "subject_name": item.subject_name,
                "level_name": item.level_name,
                "fee": format_currency(item.fee),
            }
            for item in data.selected_fees
        ],
        "other_fee_label": data.other_fee_label or "ຄ່າອື່ນໆ",
        "other_fee_amount": format_currency(data.other_fee_amount),
        "other_fee_items": other_fee_items,
        "show_other_fee": data.other_fee_amount > 0,
        "show_other_fee_items": bool(other_fee_items),
        "total_fee": format_currency(data.total_fee),
        "paid_amount": format_currency(data.cumulative_paid_amount),
        "remaining_amount": format_currency(data.remaining_amount),
        "current_payment_amount": format_currency(data.paid_amount),
        "watermark_label": "ຈ່າຍແລ້ວ" if is_fully_paid else "ຈ່າຍບາງສ່ວນ",
        "watermark_class": "is-paid" if is_fully_paid else "is-partial",
    }
