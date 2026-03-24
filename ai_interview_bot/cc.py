from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# File path
path = "UNIT3_Handwritten_Style_Notes.pdf"

# Styles
styles = getSampleStyleSheet()
hand = styles["Normal"]
hand.fontName = "Helvetica-Oblique"
hand.leading = 18

story = []

def title(text):
    story.append(Paragraph(f"<b>{text}</b>", hand))
    story.append(Spacer(1, 14))

def text(t):
    story.append(Paragraph(t.replace("\n", "<br/>"), hand))
    story.append(Spacer(1, 12))

def diag_layers():
    d = Drawing(300, 180)
    d.add(Rect(50, 130, 200, 40))
    d.add(String(80,148,"SaaS (Top Layer)", fontSize=10))
    d.add(Rect(50, 80, 200, 40))
    d.add(String(80,98,"PaaS (Middle Layer)", fontSize=10))
    d.add(Rect(50, 30, 200, 40))
    d.add(String(70,48,"IaaS (Bottom Layer)", fontSize=10))
    return d

def diag_models():
    d = Drawing(330, 140)
    d.add(Rect(10,80,90,40)); d.add(String(30,95,"Public", fontSize=10))
    d.add(Rect(120,80,90,40)); d.add(String(140,95,"Private", fontSize=10))
    d.add(Rect(230,80,90,40)); d.add(String(250,95,"Hybrid", fontSize=10))
    return d

def diag_service():
    d = Drawing(330, 180)
    d.add(Rect(30,120,260,40)); d.add(String(140,135,"SaaS", fontSize=12))
    d.add(Rect(30,70,260,40)); d.add(String(140,85,"PaaS", fontSize=12))
    d.add(Rect(30,20,260,40)); d.add(String(140,35,"IaaS", fontSize=12))
    return d

# Content generation
title("UNIT 3 – Handwritten Style Notes")
title("Layered Cloud Architecture")
text("• Three layers stack one above another.\n• IaaS → PaaS → SaaS")
story.append(diag_layers())
story.append(Spacer(1,20))

title("Cloud Deployment Models")
text("• Public = open to all\n• Private = only for one organization\n• Hybrid = mix of both")
story.append(diag_models())
story.append(Spacer(1,20))

title("Cloud Service Models")
text("• IaaS = Virtual hardware\n• PaaS = Platform for developers\n• SaaS = Ready-made apps")
story.append(diag_service())
story.append(Spacer(1,20))

title("Cloud Storage Basics")
text("• Cloud stores data online.\n• Types: Block, File, Object Storage.\n• Example: AWS S3.")

# Build PDF
doc = SimpleDocTemplate(path, pagesize=A4)
doc.build(story)

path
