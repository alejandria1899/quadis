from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


def build_pdf(movements, title: str = "Registro de movimientos"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    x_margin = 12 * mm
    y = height - 15 * mm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_margin, y, title)
    y -= 10 * mm

    c.setFont("Helvetica", 9)
    c.drawString(x_margin, y, "Hora")
    c.drawString(x_margin + 25 * mm, y, "Movimiento")
    c.drawString(x_margin + 90 * mm, y, "Comentario")
    y -= 5 * mm

    c.line(x_margin, y, width - x_margin, y)
    y -= 6 * mm

    max_comment_chars = 60

    for r in movements:
        if y < 15 * mm:
            c.showPage()
            y = height - 15 * mm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_margin, y, title)
            y -= 12 * mm
            c.setFont("Helvetica", 9)

        hhmmss = r["hhmmss"]
        name = (r["movement_name"] or "")[:30]
        comment = (r["comment"] or "")
        if len(comment) > max_comment_chars:
            comment = comment[: max_comment_chars - 3] + "..."

        c.drawString(x_margin, y, hhmmss)
        c.drawString(x_margin + 25 * mm, y, name)
        c.drawString(x_margin + 90 * mm, y, comment)
        y -= 6 * mm

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
