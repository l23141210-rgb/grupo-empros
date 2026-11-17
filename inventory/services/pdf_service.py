"""Generación de reportes PDF profesionales para Grupo Empros."""
import os
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TituloEmpros",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#0d192b"),
        spaceAfter=6,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="Subtitulo",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#4a5568"),
        alignment=TA_CENTER,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="Seccion",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#0dbaa5"),
        spaceBefore=16,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="Cuerpo",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#1d2939"),
    ))
    return styles


def generar_reporte_inventario(datos, tipo="semanal", periodo_label=""):
    """
    datos = {
        "resumen": {...},
        "productos": [...],
        "movimientos": [...],
        "bajo_minimo": [...],
    }
    """
    styles = _styles()
    filename = f"reporte_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
    )
    story = []

    # Encabezado
    story.append(Paragraph("GRUPO EMPROS", styles["TituloEmpros"]))
    story.append(Paragraph("Sistema de Gestión de Inventarios", styles["Subtitulo"]))
    story.append(Paragraph(
        f"Reporte {tipo.capitalize()} — {periodo_label or datetime.now().strftime('%d/%m/%Y')}",
        styles["Subtitulo"]
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0dbaa5"), spaceAfter=12))

    # Resumen
    resumen = datos.get("resumen", {})
    story.append(Paragraph("Resumen ejecutivo", styles["Seccion"]))

    resumen_data = [
        ["Indicador", "Valor"],
        ["Total de productos", str(resumen.get("total_productos", 0))],
        ["Piezas en inventario", f"{resumen.get('total_piezas', 0):,}"],
        ["Entradas del periodo", f"{resumen.get('entradas', 0):,}"],
        ["Salidas del periodo", f"{resumen.get('salidas', 0):,}"],
        ["Piezas vendidas (web)", f"{resumen.get('vendidas', 0):,}"],
        ["Productos bajo mínimo", str(resumen.get("bajo_minimo", 0))],
        ["Valor estimado inventario", f"${resumen.get('valor_estimado', 0):,.2f}"],
    ]
    t = Table(resumen_data, colWidths=[9*cm, 6*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d192b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f7fafc")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Productos bajo mínimo
    bajo = datos.get("bajo_minimo", [])
    if bajo:
        story.append(Paragraph("Productos bajo stock mínimo", styles["Seccion"]))
        table_data = [["Código", "Descripción", "Stock", "Mínimo"]]
        for p in bajo[:30]:
            table_data.append([
                p.get("codigo", ""),
                (p.get("descripcion") or "")[:40],
                str(p.get("stock_actual", 0)),
                str(p.get("stock_minimo", 0)),
            ])
        t2 = Table(table_data, colWidths=[3*cm, 8*cm, 2.5*cm, 2.5*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c53030")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ]))
        story.append(t2)
        story.append(Spacer(1, 12))

    # Top movimientos
    movs = datos.get("movimientos", [])
    if movs:
        story.append(Paragraph("Últimos movimientos", styles["Seccion"]))
        table_data = [["Fecha", "Tipo", "Producto", "Cantidad"]]
        for m in movs[:25]:
            table_data.append([
                m.get("fecha", "")[:16],
                m.get("tipo", "").upper(),
                (m.get("descripcion") or "")[:35],
                str(m.get("cantidad", 0)),
            ])
        t3 = Table(table_data, colWidths=[3.5*cm, 2.5*cm, 7*cm, 2.5*cm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0dbaa5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ]))
        story.append(t3)

    # Pie
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e0")))
    story.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} — Grupo Empros ©",
        styles["Subtitulo"]
    ))

    doc.build(story)
    return filename, filepath
