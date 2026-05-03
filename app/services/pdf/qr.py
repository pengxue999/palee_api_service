from base64 import b64encode

from reportlab.graphics import renderSVG
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing


def build_qr_code_data_url(value: str | None) -> str | None:
    if not value:
        return None

    widget = qr.QrCodeWidget(value)
    bounds = widget.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(width, height)
    drawing.add(widget)
    svg_markup = renderSVG.drawToString(drawing)
    encoded = b64encode(svg_markup.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"