"""生成贷款方案 PDF。使用 reportlab 内置 CJK 字体支持中文。"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from models import EnterpriseProfile, RecommendResponse

# 注册中文字体(reportlab 内置,无需外部字体文件)
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
FONT = "STSong-Light"

CREDIT_CN = {"excellent": "优秀", "good": "良好", "fair": "一般", "poor": "较差"}
PURPOSE_CN = {
    "working_capital": "流动资金周转", "equipment": "设备采购", "expansion": "扩大经营",
    "inventory": "备货采购", "rd": "研发投入", "other": "其他",
}


def _styles():
    ss = getSampleStyleSheet()
    base = ParagraphStyle("cn", parent=ss["Normal"], fontName=FONT, fontSize=10,
                          leading=15, alignment=TA_LEFT)
    title = ParagraphStyle("cn_title", parent=base, fontSize=20, leading=26,
                           textColor=colors.HexColor("#1e40af"), spaceAfter=4)
    sub = ParagraphStyle("cn_sub", parent=base, fontSize=9,
                         textColor=colors.HexColor("#6b7280"))
    h2 = ParagraphStyle("cn_h2", parent=base, fontSize=13, leading=18,
                        textColor=colors.HexColor("#111827"), spaceBefore=10, spaceAfter=6)
    small = ParagraphStyle("cn_small", parent=base, fontSize=9, leading=13,
                           textColor=colors.HexColor("#374151"))
    return base, title, sub, h2, small


def build_pdf(profile: EnterpriseProfile, result: RecommendResponse) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=16 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            title="中小微企业贷款方案报告")
    base, title, sub, h2, small = _styles()
    el = []

    name = profile.company_name or "企业"
    el.append(Paragraph("中小微企业贷款方案报告", title))
    el.append(Paragraph(f"{name} · 生成时间 {datetime.now().strftime('%Y-%m-%d %H:%M')}", sub))
    el.append(Spacer(1, 8))

    # 摘要
    el.append(Paragraph("一、方案摘要", h2))
    el.append(Paragraph(result.summary, base))

    # 企业画像
    el.append(Paragraph("二、企业画像", h2))
    prof_rows = [
        ["所属行业", profile.industry, "经营年限", f"{profile.years_in_business} 年"],
        ["年营业额", f"{profile.annual_revenue} 万元", "注册资本", f"{profile.registered_capital} 万元"],
        ["员工人数", f"{profile.employees} 人", "征信状况", CREDIT_CN.get(profile.credit_level.value, "-")],
        ["贷款需求", f"{profile.loan_amount} 万元", "贷款用途", PURPOSE_CN.get(profile.loan_purpose.value, "-")],
        ["期望期限", f"{profile.preferred_term_months} 个月",
         "抵押物", f"{profile.collateral_value} 万元" if profile.has_collateral else "无"],
    ]
    t = Table(prof_rows, colWidths=[28 * mm, 50 * mm, 28 * mm, 50 * mm])
    t.setStyle(_kv_style())
    el.append(t)

    # 风险评估
    r = result.risk
    el.append(Paragraph("三、风控评估", h2))
    el.append(Paragraph(
        f"综合风控评分:<b>{r.score}</b> / 100  ·  风险等级:<b>{r.grade}（{r.grade_label}）</b>"
        + (f"  ·  负债杠杆:{int(r.debt_ratio*100)}%" if r.debt_ratio is not None else ""), base))
    el.append(Spacer(1, 4))
    factor_rows = [["风险因子", "影响", "说明"]]
    impact_cn = {"positive": "正向", "negative": "负向", "neutral": "中性"}
    for f in r.factors:
        factor_rows.append([f.name, impact_cn.get(f.impact, f.impact),
                            Paragraph(f.detail, small)])
    ft = Table(factor_rows, colWidths=[26 * mm, 16 * mm, 114 * mm])
    ft.setStyle(_table_style())
    el.append(ft)

    # 推荐方案
    el.append(Paragraph("四、推荐贷款方案", h2))
    if result.plans:
        head = ["排名", "产品", "额度(万)", "年化利率", "期限", "月供(万)", "通过率", "匹配分"]
        rows = [head]
        for i, p in enumerate(result.plans, 1):
            rows.append([
                ("★1" if i == 1 else str(i)), p.product_name, f"{p.estimated_amount}",
                f"{p.annual_rate_min}%-{p.annual_rate_max}%", f"{p.suggested_term_months}月",
                f"{p.monthly_payment_estimate}", p.approval_probability, str(p.score),
            ])
        pt = Table(rows, colWidths=[12 * mm, 34 * mm, 18 * mm, 26 * mm, 14 * mm, 18 * mm, 16 * mm, 14 * mm])
        pt.setStyle(_table_style(highlight_first_row=True))
        el.append(pt)
        el.append(Spacer(1, 4))
        best = result.plans[0]
        el.append(Paragraph(f"最优推荐【{best.product_name}】推荐理由:", small))
        for reason in best.match_reasons:
            el.append(Paragraph(f"· {reason}", small))
    else:
        el.append(Paragraph("当前资质暂未匹配到合适产品,请参考提升建议。", base))

    # 个性化建议
    if result.personalized_advice:
        el.append(Paragraph("五、个性化融资建议", h2))
        for a in result.personalized_advice:
            el.append(Paragraph(f"· {a}", small))

    # 补贴政策
    if result.subsidies:
        el.append(Paragraph("六、可申报扶持政策", h2))
        srows = [["政策名称", "类别", "主管部门", "扶持内容"]]
        for s in result.subsidies:
            srows.append([Paragraph(s.name, small), s.category, s.authority,
                          Paragraph(s.benefit, small)])
        st = Table(srows, colWidths=[34 * mm, 22 * mm, 30 * mm, 70 * mm])
        st.setStyle(_table_style())
        el.append(st)

    # 提升建议
    if result.improvement_tips:
        el.append(Paragraph("七、资质提升建议", h2))
        for tip in result.improvement_tips:
            el.append(Paragraph(f"· {tip}", small))

    el.append(Spacer(1, 12))
    el.append(Paragraph(
        "免责声明:本报告中的额度、利率、月供及政策匹配均为基于公开规则的估算与示意,"
        "仅供参考,实际以金融机构审批结果及主管部门最新政策为准。", sub))

    doc.build(el)
    buf.seek(0)
    return buf.read()


def _kv_style():
    return TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f3f4f6")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4b5563")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#4b5563")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])


def _table_style(highlight_first_row=False):
    style = [
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]
    if highlight_first_row:
        style.append(("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fef3c7")))
    return TableStyle(style)
