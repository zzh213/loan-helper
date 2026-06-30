"""生成「申请进度汇总」PDF 报表,汇总全部申请记录的状态分布与额度统计。"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from pdf_export import FONT, _styles

STATUS_LIST = ["待提交", "已提交", "审核中", "已通过", "已拒绝", "已放款"]


def build_records_summary(records: list, hidden: list = None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=16 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            title="申请进度汇总报表")
    base, title, sub, h2, small = _styles()
    el = []

    total = len(records)
    counts = {s: 0 for s in STATUS_LIST}
    demand = 0
    approved_amt = 0
    for r in records:
        counts[r.get("status", "待提交")] = counts.get(r.get("status", "待提交"), 0) + 1
        demand += r.get("loan_amount", 0) or 0
        if r.get("status") in ("已通过", "已放款"):
            approved_amt += r.get("best_amount", 0) or 0
    done = counts["已通过"] + counts["已放款"]
    closed = done + counts["已拒绝"]
    approve_rate = round(done / closed * 100) if closed else 0
    avg = round(demand / total) if total else 0

    el.append(Paragraph("申请进度汇总报表", title))
    el.append(Paragraph(f"生成时间 {datetime.now().strftime('%Y-%m-%d %H:%M')} · 共 {total} 笔申请", sub))
    el.append(Spacer(1, 10))

    cards = [["申请总数", "进行中", "已获批", "需求合计", "预计获贷"],
             [str(total), str(counts["已提交"] + counts["审核中"]), f"{done}({approve_rate}%)",
              f"{demand}万", f"{approved_amt}万"]]
    t = Table(cards, colWidths=[36 * mm] * 5)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, 0), 9), ("FONTSIZE", (0, 1), (-1, 1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#6b7280")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#1e40af")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f6")),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
    ]))
    el.append(t)
    el.append(Spacer(1, 12))

    el.append(Paragraph("一、状态分布", h2))
    rows = [["状态", "数量", "占比"]]
    for s in STATUS_LIST:
        pct = round(counts[s] / total * 100) if total else 0
        rows.append([s, str(counts[s]), f"{pct}%"])
    st = Table(rows, colWidths=[60 * mm, 40 * mm, 40 * mm])
    st.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT), ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8cacd2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    el.append(st)
    el.append(Spacer(1, 12))

    el.append(Paragraph("二、申请明细", h2))
    det = [["企业", "行业", "需求(万)", "推荐产品", "额度(万)", "风控", "状态"]]
    for r in records:
        det.append([r.get("company_name", ""), r.get("industry", ""), str(r.get("loan_amount", "")),
                    r.get("best_product", ""), str(r.get("best_amount", "")),
                    f"{r.get('risk_score','')}{r.get('risk_grade','')}", r.get("status", "")])
    dt = Table(det, colWidths=[28*mm, 20*mm, 18*mm, 32*mm, 18*mm, 22*mm, 18*mm])
    dt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT), ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f6")),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    el.append(dt)

    if hidden:
        cell = ParagraphStyle("cell", parent=small, fontSize=8, leading=11)
        el.append(Spacer(1, 14))
        el.append(Paragraph("三、园区/区县独家隐藏贴息库(独家信息差)", h2))
        el.append(Paragraph("以下为通用搜索引擎/AI 检索不到的非公开园区、区县级贴息,可按企业地址定向申报。", small))
        el.append(Spacer(1, 6))
        hr = [["所在地区", "政策名称", "最高额", "贴息", "扶持内容/申报路径"]]
        for s in hidden:
            hr.append([Paragraph(s.get("region", ""), cell), Paragraph(s.get("name", ""), cell),
                       f"{s.get('amount_max','-')}万", f"{s.get('rate_subsidy','-')}%",
                       Paragraph(f"{s.get('benefit','')}<br/>申报:{s.get('apply_points','')}", cell)])
        ht = Table(hr, colWidths=[26*mm, 32*mm, 14*mm, 12*mm, 70*mm])
        ht.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), FONT), ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8cacd2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (2, 0), (3, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        el.append(ht)

    doc.build(el)
    return buf.getvalue()
