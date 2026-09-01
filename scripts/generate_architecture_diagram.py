#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "architecture-diagram.png"
W, H = 1600, 900
img = Image.new("RGB", (W, H), "#FFFFFF")
d = ImageDraw.Draw(img)
REG = "/usr/share/fonts/msttcore/arial.ttf"
BOLD = "/usr/share/fonts/msttcore/arialbd.ttf"

def font(size: int, bold: bool = False):
    return ImageFont.truetype(BOLD if bold else REG, size)

def rounded(box, fill, outline="#E6E5E3", width=2, radius=18):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def text(x, y, value, size=24, color="#2C2C2B", bold=False, anchor="la"):
    d.text((x, y), value, font=font(size, bold), fill=color, anchor=anchor)

def line(points, color="#2783DE", width=5):
    d.line(points, fill=color, width=width, joint="curve")
    x1, y1 = points[-2]; x2, y2 = points[-1]
    if abs(x2-x1) >= abs(y2-y1):
        s = 1 if x2 > x1 else -1
        d.polygon([(x2,y2),(x2-14*s,y2-8),(x2-14*s,y2+8)], fill=color)
    else:
        s = 1 if y2 > y1 else -1
        d.polygon([(x2,y2),(x2-8,y2-14*s),(x2+8,y2-14*s)], fill=color)

# Header
text(70, 58, "RecallReady", 42, "#2C2C2B", True)
text(70, 108, "Food-bank recall closure agent · submission architecture", 22, "#7D7A75")
d.line((70, 145, 1530, 145), fill="#E6E5E3", width=2)

# Sources
rounded((70, 220, 330, 620), "#F9F8F7")
text(100, 255, "Triggers & people", 24, bold=True)
for i, (title, sub) in enumerate([
    ("Recall source", "PDF · JSON · text · FDA"),
    ("Pub/Sub event", "Authenticated push + retries"),
    ("Operator", "Review · acknowledge · verify"),
    ("Partner pantry", "Task evidence + confirmation"),
]):
    y = 315 + i*72
    d.ellipse((100, y, 116, y+16), fill="#2783DE")
    text(132, y+1, title, 20, bold=True)
    text(132, y+27, sub, 15, "#7D7A75")

# Main Cloud Run boundary
rounded((435, 190, 1035, 695), "#E5F2FC", "#2783DE", 3, 24)
text(470, 228, "Google Cloud Run", 28, "#1C5F9E", True)
text(470, 265, "Canonical backend · required Google Cloud proof", 17, "#1C5F9E")

rounded((480, 315, 990, 405), "#FFFFFF")
text(510, 342, "FastAPI + Jinja operations console", 23, bold=True)
text(510, 375, "Ingestion · tasks · evidence · readiness · audit", 17, "#7D7A75")

rounded((480, 435, 990, 535), "#FFFFFF")
text(510, 462, "RecallCoordinatorAgent · Google ADK 2.7.1", 22, bold=True)
text(510, 496, "8 typed read/proposal tools · bounded model authority", 17, "#7D7A75")

rounded((480, 565, 990, 650), "#FFFFFF")
text(510, 590, "Deterministic workflow & safety policy", 22, bold=True)
text(510, 622, "Exact hold · human review · blockers · idempotency", 17, "#7D7A75")

# Inputs to Cloud Run
line([(330, 420), (435, 420)], "#2783DE")
text(382, 400, "HTTPS", 15, "#1C5F9E", True, "mm")

# Gemini
rounded((1120, 185, 1515, 320), "#FBEBDE", "#D5803B", 3)
text(1155, 220, "Gemini 3.7 Flash", 26, "#8B4E1F", True)
text(1155, 258, "Schema-constrained extraction", 18, "#8B4E1F")
text(1155, 286, "Interpretation—not write authority", 16, "#7D7A75")
line([(1035, 355), (1080, 355), (1080, 252), (1120, 252)], "#D5803B")

# GCP data plane
rounded((1090, 370, 1515, 695), "#E8F1EC", "#46A171", 3, 22)
text(1125, 405, "Google Cloud data plane", 25, "#2F7653", True)
services = [
    ("Firestore", "Durable state + transactions"),
    ("Cloud Storage", "Private evidence objects"),
    ("Pub/Sub", "At-least-once + dead letter"),
    ("Secret Manager", "Runtime secrets"),
    ("Cloud Logging", "Correlated proof of execution"),
]
for i, (title, sub) in enumerate(services):
    y = 452 + i*48
    d.rounded_rectangle((1125, y, 1141, y+16), radius=4, fill="#46A171")
    text(1160, y-3, title, 17, bold=True)
    text(1160, y+19, sub, 14, "#557064")
line([(1035, 570), (1090, 570)], "#46A171")

# Outputs
rounded((70, 695, 1035, 805), "#F9F8F7")
text(100, 728, "Proof of action", 23, bold=True)
text(275, 728, "Reversible hold", 16, "#2F7653", True)
text(455, 728, "Human review", 16, "#8B4E1F", True)
text(620, 728, "Partner ack", 16, "#1C5F9E", True)
text(770, 728, "Evidence ZIP", 16, "#2C2C2B", True)
text(100, 770, "Every state change is auditable; INTERNAL_CLOSED never means regulator closure.", 18, "#7D7A75")
line([(735, 695), (735, 650)], "#2783DE")

# Optional Vercel mirror
rounded((1090, 735, 1515, 820), "#F9F8F7", "#B9B6B1", 2, 16)
text(1120, 760, "Optional Vercel judge preview", 19, bold=True)
text(1120, 790, "Public mirror · ephemeral unless Firestore-backed", 15, "#7D7A75")

# Footer labels
text(70, 855, "Blue = application runtime    Green = durable Google Cloud services    Orange = Gemini reasoning", 16, "#7D7A75")
text(1530, 855, "v1.3.0", 16, "#7D7A75", True, "ra")

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, optimize=True)
print(f"{OUT} {OUT.stat().st_size} bytes {W}x{H}")
