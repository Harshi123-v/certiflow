import math
from pathlib import Path
from typing import Dict, Any
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# Page Dimensions (Landscape Letter: 11 x 8.5 in -> 792 x 612 pt)
PAGE_WIDTH, PAGE_HEIGHT = landscape(letter)

# Color Palette: Navy, Ivory, Gold, Charcoal
COLOR_IVORY_BG = HexColor("#FCFBF7")
COLOR_NAVY_DARK = HexColor("#0A192F")
COLOR_NAVY_LIGHT = HexColor("#1E3A8A")
COLOR_GOLD_PRIMARY = HexColor("#C5A059")
COLOR_GOLD_ACCENT = HexColor("#D4AF37")
COLOR_GOLD_DARK = HexColor("#997D3D")
COLOR_TEXT_MUTED = HexColor("#4A5568")
COLOR_TEXT_LIGHT = HexColor("#718096")
COLOR_BORDER_LIGHT = HexColor("#E2E8F0")

def draw_corner_ornament(c: canvas.Canvas, x: float, y: float, angle: float):
    """Draws an elegant corner bracket/flourish in gold."""
    c.saveState()
    c.translate(x, y)
    c.rotate(angle)
    c.setStrokeColor(COLOR_GOLD_PRIMARY)
    c.setFillColor(COLOR_GOLD_PRIMARY)
    c.setLineWidth(1.5)
    
    # L-bracket lines
    c.line(0, 0, 30, 0)
    c.line(0, 0, 0, 30)
    c.line(6, 6, 24, 6)
    c.line(6, 6, 6, 24)
    
    # Small corner diamond
    path = c.beginPath()
    path.moveTo(0, 0)
    path.lineTo(4, -4)
    path.lineTo(8, 0)
    path.lineTo(4, 4)
    path.close()
    c.drawPath(path, fill=1, stroke=0)
    
    c.restoreState()

def draw_borders(c: canvas.Canvas):
    """Draws a multi-layered gold and deep navy border."""
    # 1. Background fill
    c.setFillColor(COLOR_IVORY_BG)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

    # 2. Outer thin gold border
    c.setStrokeColor(COLOR_GOLD_PRIMARY)
    c.setLineWidth(1.5)
    c.rect(20, 20, PAGE_WIDTH - 40, PAGE_HEIGHT - 40, fill=0, stroke=1)

    # 3. Middle solid navy border
    c.setStrokeColor(COLOR_NAVY_DARK)
    c.setLineWidth(5)
    c.rect(28, 28, PAGE_WIDTH - 56, PAGE_HEIGHT - 56, fill=0, stroke=1)

    # 4. Inner delicate gold double border
    c.setStrokeColor(COLOR_GOLD_PRIMARY)
    c.setLineWidth(0.8)
    c.rect(38, 38, PAGE_WIDTH - 76, PAGE_HEIGHT - 76, fill=0, stroke=1)
    c.rect(42, 42, PAGE_WIDTH - 84, PAGE_HEIGHT - 84, fill=0, stroke=1)

    # 5. Corner ornaments
    draw_corner_ornament(c, 44, PAGE_HEIGHT - 44, 0)
    draw_corner_ornament(c, PAGE_WIDTH - 44, PAGE_HEIGHT - 44, -90)
    draw_corner_ornament(c, PAGE_WIDTH - 44, 44, -180)
    draw_corner_ornament(c, 44, 44, 90)

def draw_seal(c: canvas.Canvas, cx: float, cy: float, radius: float = 38):
    """Draws an official vector gold emblem/seal with rosette and ribbon."""
    c.saveState()
    
    # Outer starburst / serrated edge
    points = 36
    inner_r = radius - 3
    outer_r = radius
    star_path = c.beginPath()
    for i in range(points * 2):
        r = outer_r if i % 2 == 0 else inner_r
        angle = i * math.pi / points
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        if i == 0:
            star_path.moveTo(px, py)
        else:
            star_path.lineTo(px, py)
    star_path.close()
    c.setFillColor(COLOR_GOLD_ACCENT)
    c.setStrokeColor(COLOR_GOLD_DARK)
    c.setLineWidth(0.8)
    c.drawPath(star_path, fill=1, stroke=1)

    # Inner concentric rings
    c.setStrokeColor(COLOR_NAVY_DARK)
    c.setLineWidth(1)
    c.circle(cx, cy, radius - 8, fill=0, stroke=1)
    
    c.setFillColor(COLOR_IVORY_BG)
    c.circle(cx, cy, radius - 10, fill=1, stroke=0)

    c.setStrokeColor(COLOR_GOLD_PRIMARY)
    c.setLineWidth(0.8)
    c.circle(cx, cy, radius - 12, fill=0, stroke=1)

    # Center Star
    c.setFillColor(COLOR_GOLD_DARK)
    c.setStrokeColor(COLOR_GOLD_DARK)
    star5 = c.beginPath()
    for i in range(10):
        r = (radius - 22) if i % 2 == 0 else (radius - 30)
        angle = i * math.pi / 5 - math.pi / 2
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        if i == 0:
            star5.moveTo(px, py)
        else:
            star5.lineTo(px, py)
    star5.close()
    c.drawPath(star5, fill=1, stroke=0)

    # Mini text in seal
    c.setFont("Helvetica-Bold", 4.5)
    c.setFillColor(COLOR_NAVY_DARK)
    c.drawCentredString(cx, cy + 14, "★ OFFICIAL ★")
    c.drawCentredString(cx, cy - 18, "EXCELLENCE")

    c.restoreState()

def draw_signature(c: canvas.Canvas, x: float, y: float):
    """Draws an elegant realistic calligraphy-style signature flourish."""
    c.saveState()
    c.setStrokeColor(COLOR_NAVY_DARK)
    c.setLineWidth(1.4)
    c.setLineCap(1)  # Round cap
    c.setLineJoin(1) # Round join
    
    # Smooth bezier curves creating an executive signature
    p = c.beginPath()
    p.moveTo(x, y + 6)
    p.curveTo(x + 10, y + 25, x + 18, y + 28, x + 24, y + 12)
    p.curveTo(x + 28, y + 2, x + 35, y + 4, x + 42, y + 18)
    p.curveTo(x + 48, y + 30, x + 58, y + 8, x + 68, y + 14)
    p.curveTo(x + 78, y + 20, x + 88, y + 16, x + 100, y + 8)
    # Underline flourish
    p.curveTo(x + 115, y - 2, x + 40, y - 6, x + 20, y - 2)
    p.curveTo(x + 50, y - 4, x + 90, y - 2, x + 130, y - 1)
    c.drawPath(p, fill=0, stroke=1)
    
    c.restoreState()

def fit_text_font_size(
    c: canvas.Canvas,
    text: str,
    font_name: str,
    max_font_size: float,
    min_font_size: float,
    max_width: float
) -> float:
    """Calculates maximum font size that fits text within max_width."""
    font_size = max_font_size
    while font_size >= min_font_size:
        if c.stringWidth(text, font_name, font_size) <= max_width:
            return font_size
        font_size -= 1.0
    return min_font_size

def render_certificate_pdf(
    output_path: Path,
    cert_data: Dict[str, Any],
    recipient_data: Dict[str, Any]
) -> None:
    """
    Renders a landscape letter PDF certificate according to specifications.
    Uses safe fallback fonts (Standard 14 PDF fonts: Helvetica, Times-Roman).
    """
    c = canvas.Canvas(str(output_path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    # 1. Background & borders
    draw_borders(c)

    cx = PAGE_WIDTH / 2.0

    # 2. Issuing Organization Header
    org_name = (cert_data.get("organization_name") or "AERO LEARNING ACADEMY").upper()
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(COLOR_GOLD_DARK)
    c.drawCentredString(cx, PAGE_HEIGHT - 80, org_name)

    # Small top divider
    c.setStrokeColor(COLOR_GOLD_PRIMARY)
    c.setLineWidth(0.8)
    c.line(cx - 70, PAGE_HEIGHT - 90, cx + 70, PAGE_HEIGHT - 90)

    # 3. Certificate Title
    title = (cert_data.get("title") or "CERTIFICATE OF COMPLETION").upper()
    title_font_size = fit_text_font_size(c, title, "Helvetica-Bold", 26, 18, PAGE_WIDTH - 200)
    c.setFont("Helvetica-Bold", title_font_size)
    c.setFillColor(COLOR_NAVY_DARK)
    c.drawCentredString(cx, PAGE_HEIGHT - 128, title)

    # 4. Presentation line
    c.setFont("Helvetica", 11)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawCentredString(cx, PAGE_HEIGHT - 164, "THIS IS PROUDLY PRESENTED TO")

    # 5. Recipient Name (with dynamic font sizing for long names)
    recipient_name = recipient_data.get("name", "Recipient Name")
    name_font_size = fit_text_font_size(c, recipient_name, "Times-BoldItalic", 32, 18, PAGE_WIDTH - 220)
    c.setFont("Times-BoldItalic", name_font_size)
    c.setFillColor(COLOR_NAVY_LIGHT)
    c.drawCentredString(cx, PAGE_HEIGHT - 212, recipient_name)

    # Fine gold underline below recipient name
    name_width = min(c.stringWidth(recipient_name, "Times-BoldItalic", name_font_size) + 40, PAGE_WIDTH - 220)
    c.setStrokeColor(COLOR_GOLD_PRIMARY)
    c.setLineWidth(1)
    c.line(cx - (name_width / 2.0), PAGE_HEIGHT - 222, cx + (name_width / 2.0), PAGE_HEIGHT - 222)

    # 6. Curriculum / Statement of Achievement
    c.setFont("Helvetica", 10.5)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawCentredString(
        cx,
        PAGE_HEIGHT - 254,
        "for successfully demonstrating excellence and completing all requirements for"
    )

    # 7. Course / Event Name
    course_name = cert_data.get("course_name") or "Advanced Professional Program"
    course_font_size = fit_text_font_size(c, course_name, "Helvetica-Bold", 19, 13, PAGE_WIDTH - 240)
    c.setFont("Helvetica-Bold", course_font_size)
    c.setFillColor(COLOR_NAVY_DARK)
    c.drawCentredString(cx, PAGE_HEIGHT - 288, course_name)

    # 8. Bottom Information Section:
    # Left: Issue Date & Certificate ID & Verification
    left_x = 75
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(COLOR_NAVY_DARK)
    c.drawString(left_x, 155, "DATE OF ISSUANCE")
    
    completion_date = str(cert_data.get("completion_date", "2026-10-09"))
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(left_x, 140, completion_date)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(COLOR_NAVY_DARK)
    c.drawString(left_x, 115, "CERTIFICATE ID")
    
    cert_id = str(recipient_data.get("certificate_id", "CERT-0000-000"))
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(COLOR_GOLD_DARK)
    c.drawString(left_x, 100, cert_id)

    c.setFont("Helvetica", 7.5)
    c.setFillColor(COLOR_TEXT_LIGHT)
    c.drawString(left_x, 82, "Digitally verified via CertiFlow Verification Engine")

    # Center: Official Seal / Medallion
    draw_seal(c, cx, 122, radius=40)

    # Right: Signature & Signatory block
    right_x = PAGE_WIDTH - 215
    draw_signature(c, right_x, 135)

    # Signature line
    c.setStrokeColor(COLOR_NAVY_DARK)
    c.setLineWidth(1)
    c.line(right_x - 10, 125, right_x + 140, 125)

    signatory_name = cert_data.get("signatory_name", "Program Director")
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(COLOR_NAVY_DARK)
    c.drawCentredString(right_x + 65, 110, signatory_name)

    signatory_title = cert_data.get("signatory_title", "Authorized Signatory")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawCentredString(right_x + 65, 96, signatory_title)

    # Save PDF
    c.showPage()
    c.save()
