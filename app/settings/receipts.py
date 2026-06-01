from __future__ import annotations

import io
import os
import textwrap
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.utils import timezone

from .models import Payment


def _money(amount) -> str:
    value = Decimal(str(amount or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{value:.2f} KGS"


def _brand_name(payment: Payment, fallback: str | None = None) -> str:
    for org in (
        getattr(payment, "organization", None),
        getattr(getattr(payment, "course", None), "organization", None),
        getattr(getattr(payment, "student", None), "organization", None),
    ):
        name = (getattr(org, "name", "") or "").strip()
        if name:
            return name

    jazzmin = getattr(settings, "JAZZMIN_SETTINGS", {}) or {}
    return (fallback or jazzmin.get("site_brand") or jazzmin.get("site_header") or "American Dream").strip()


def _font_paths():
    base = os.path.dirname(__file__)
    return [
        (
            os.path.join(base, "static", "crm_dashboard", "fonts", "DejaVuSans.ttf"),
            os.path.join(base, "static", "crm_dashboard", "fonts", "DejaVuSans-Bold.ttf"),
        ),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
        (
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        ),
        (
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
        ),
        (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ),
    ]


def _receipt_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    regular_name = "CRMReceiptRegular"
    bold_name = "CRMReceiptBold"
    registered = set(pdfmetrics.getRegisteredFontNames())
    if regular_name in registered:
        return regular_name, bold_name if bold_name in registered else regular_name

    for regular_path, bold_path in _font_paths():
        if not os.path.exists(regular_path):
            continue
        pdfmetrics.registerFont(TTFont(regular_name, regular_path))
        if os.path.exists(bold_path):
            pdfmetrics.registerFont(TTFont(bold_name, bold_path))
            return regular_name, bold_name
        return regular_name, regular_name
    return "Helvetica", "Helvetica-Bold"


def _draw_dashed_line(canvas, x1, y, x2):
    canvas.saveState()
    canvas.setDash(5, 4)
    canvas.setStrokeColorRGB(0.82, 0.82, 0.82)
    canvas.line(x1, y, x2, y)
    canvas.restoreState()


def _draw_wrapped(canvas, text, x, y, font_name, font_size, max_chars, line_gap):
    lines = textwrap.wrap((text or "").strip() or "-", width=max_chars) or ["-"]
    canvas.setFont(font_name, font_size)
    for line in lines[:3]:
        canvas.drawString(x, y, line)
        y -= line_gap
    return y


def payment_receipt_pdf(payment: Payment, brand_name: str | None = None) -> bytes:
    from reportlab.lib.pagesizes import A6
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    regular_font, bold_font = _receipt_fonts()
    brand = brand_name or _brand_name(payment)
    subtitle = brand
    student_user = payment.student.user
    client_name = student_user.get_full_name() or student_user.username
    course_title = payment.course.title if payment.course_id else "Оплата"
    dt = timezone.localtime(payment.created_at).strftime("%d.%m.%Y %H:%M") if payment.created_at else ""

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A6)
    width, height = A6
    margin = 10 * mm
    right = width - margin
    y = height - margin

    c.setFillColorRGB(0, 0, 0)
    c.setFont(bold_font, 15)
    c.drawString(margin, y, brand[:34])
    y -= 8 * mm
    c.setFont(regular_font, 12)
    c.drawString(margin, y, subtitle[:42])
    y -= 12 * mm

    c.setFont(bold_font, 16)
    c.drawString(margin, y, f"Чек #{payment.pk}")
    c.setFont(bold_font, 13)
    c.drawRightString(right, y, dt)
    y -= 8 * mm
    _draw_dashed_line(c, margin, y, right)
    y -= 9 * mm

    c.setFont(bold_font, 14)
    c.drawString(margin, y, "Наименование")
    c.drawRightString(right, y, "Сумма")
    y -= 7 * mm
    _draw_dashed_line(c, margin, y, right)
    y -= 8 * mm

    item_y = y
    y = _draw_wrapped(c, course_title, margin, y, bold_font, 11, 26, 5 * mm)
    c.setFont(bold_font, 11)
    c.drawRightString(right, item_y, _money(payment.amount))

    y = min(y, 54 * mm)
    if y > 44 * mm:
        y = 44 * mm
    _draw_dashed_line(c, margin, y, right)
    y -= 7 * mm

    c.setFont(bold_font, 10)
    c.drawString(margin, y, f"Способ оплаты: {payment.get_method_display()}")
    y -= 5 * mm
    c.drawString(margin, y, f"Клиент: {client_name[:32]}")
    y -= 8 * mm
    _draw_dashed_line(c, margin, y, right)
    y -= 8 * mm

    c.setFont(bold_font, 15)
    c.drawString(margin, y, "Итого:")
    c.drawRightString(right, y, _money(payment.amount))
    y -= 8 * mm
    _draw_dashed_line(c, margin, y, right)
    y -= 8 * mm

    c.setFont(bold_font, 12)
    c.drawString(margin, y, brand[:38])
    y -= 7 * mm
    c.setFont(regular_font, 10)
    c.drawString(margin, y, "Codify LMS")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
