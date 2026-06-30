"""一键生成可直接提交银行的成品材料 PDF(多页打包):
  1) 授信申请表(适配最优推荐银行模板风格)
  2) 经营情况说明书
  3) 财政贴息申报台账
字段自动从企业画像与推荐结果填充,公司可下载后微调盖章提交。
"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from models import EnterpriseProfile, RecommendResponse

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
FONT = "STSong-Light"

CREDIT_CN = {"excellent": "优秀", "good": "良好", "fair": "一般", "poor": "较差"}
PURPOSE_CN = {
    "working_capital": "流动资金周转", "equipment": "设备采购", "expansion": "扩大经营",
    "inventory": "备货采购", "rd": "研发投入", "other": "其他",
}

# 不同银行类型的模板主色,生成的材料带有对应银行风格
BANK_THEME = {
    "国有银行": "#9a1f1f",
    "股份制银行": "#1e40af",
    "城商行": "#0f766e",
    "政策性/普惠": "#b45309",
    "互联网银行": "#6d28d9",
    "小额贷款公司": "#374151",
}

# 主流银行专属模板主色,导出材料按所选银行抬头与配色生成
BANKS = {
    "工商银行": "#9a1f1f", "建设银行": "#1e3a8a", "农业银行": "#15803d",
    "中国银行": "#9a1f1f", "邮储银行": "#15803d", "招商银行": "#b91c1c",
    "民生银行": "#0f766e", "本地城商行": "#0f766e", "微众银行": "#6d28d9",
    "网商银行": "#6d28d9",
}


def _styles(theme: str):
    main = colors.HexColor(theme)
    ss = getSampleStyleSheet()
    base = ParagraphStyle("cn", parent=ss["Normal"], fontName=FONT, fontSize=10,
                          leading=15, alignment=TA_LEFT)
    title = ParagraphStyle("t", parent=base, fontSize=19, leading=24,
                           alignment=TA_CENTER, textColor=main, spaceAfter=2)
    sub = ParagraphStyle("s", parent=base, fontSize=9, alignment=TA_CENTER,
                         textColor=colors.HexColor("#6b7280"), spaceAfter=8)
    h2 = ParagraphStyle("h2", parent=base, fontSize=12, leading=17, textColor=main,
                        spaceBefore=10, spaceAfter=5)
    small = ParagraphStyle("sm", parent=base, fontSize=9, leading=14,
                           textColor=colors.HexColor("#374151"))
    cell = ParagraphStyle("c", parent=base, fontSize=9, leading=13)
    return base, title, sub, h2, small, cell


def _kv_style():
    return TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f3f4f6")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4b5563")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#4b5563")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])


def _grid_style(theme):
    return TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(theme)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])


def build_bank_package(profile: EnterpriseProfile, result: RecommendResponse, hidden=None, bank_name="") -> bytes:
    best = result.plans[0] if result.plans else None
    theme = BANKS.get(bank_name) or BANK_THEME.get(best.provider_type if best else "", "#1e40af")
    base, title, sub, h2, small, cell = _styles(theme)
    company = profile.company_name or "(请填写企业名称)"
    today = datetime.now().strftime("%Y 年 %m 月 %d 日")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=16 * mm, bottomMargin=14 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            title="银行成品申报材料")
    el = []
    if bank_name:
        el.append(Paragraph(f"致:{bank_name} 普惠金融部", h2))
    el += _form_credit(profile, result, best, theme, title, sub, h2, base, small, cell)
    el.append(PageBreak())
    el += _form_statement(profile, result, best, theme, title, sub, h2, base, small, company, today)
    el.append(PageBreak())
    el += _form_subsidy_ledger(profile, result, theme, title, sub, h2, base, small, cell, company, today, hidden)
    doc.build(el)
    buf.seek(0)
    return buf.read()


def _logo_box(theme):
    """企业 Logo 占位框,供盖章/贴 Logo 用。"""
    t = Table([["企业\nLogo"]], colWidths=[24 * mm], rowHeights=[24 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#9ca3af")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(theme)),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _header(theme, title, sub, doc_title, sub_text):
    """Logo 占位 + 居中标题。"""
    title_cell = [Paragraph(doc_title, title), Paragraph(sub_text, sub)]
    head = Table([[_logo_box(theme), title_cell]], colWidths=[28 * mm, 148 * mm])
    head.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return head


def _signature(today):
    rows = [["企业(公章):________________", "法定代表人(签字):________________"],
            [f"申报日期:{today}", "联系电话:________________"]]
    t = Table(rows, colWidths=[88 * mm, 88 * mm])
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), FONT),
                           ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                           ("TOPPADDING", (0, 0), (-1, -1), 10),
                           ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#374151"))]))
    return t


def _form_credit(profile, result, best, theme, title, sub, h2, base, small, cell):
    el = [_header(theme, title, sub, "企业授信申请表",
                  f"申请机构:{best.provider_type if best else '——'} · "
                  f"拟申请产品:{best.product_name if best else '——'}"),
          Spacer(1, 6)]
    el.append(Paragraph("一、申请人基本信息", h2))
    rows = [
        ["企业名称", profile.company_name or "", "所属行业", profile.industry],
        ["经营年限", f"{profile.years_in_business} 年", "员工人数", f"{profile.employees} 人"],
        ["注册资本", f"{profile.registered_capital} 万元", "年营业额", f"{profile.annual_revenue} 万元"],
        ["征信状况", CREDIT_CN.get(profile.credit_level.value, "-"),
         "纳税记录", "有" if profile.has_tax_record else "无"],
        ["开票流水", "有" if profile.has_invoice else "无",
         "当前逾期", "有" if profile.has_overdue else "无"],
    ]
    t = Table(rows, colWidths=[26 * mm, 60 * mm, 26 * mm, 60 * mm])
    t.setStyle(_kv_style())
    el.append(t)

    el.append(Paragraph("二、授信申请要素", h2))
    amount = best.estimated_amount if best else profile.loan_amount
    rate = f"{best.annual_rate_min}%-{best.annual_rate_max}%" if best else "——"
    term = best.suggested_term_months if best else profile.preferred_term_months
    monthly = best.monthly_payment_estimate if best else "——"
    rows2 = [
        ["申请额度", f"{amount} 万元", "申请期限", f"{term} 个月"],
        ["资金用途", PURPOSE_CN.get(profile.loan_purpose.value, "-"), "预计年化利率", rate],
        ["还款方式", "等额本息", "预估月供", f"{monthly} 万元"],
        ["担保方式", ("抵押(估值 %s 万元)" % profile.collateral_value) if profile.has_collateral else "信用",
         "预计放款", best.expected_release_days if best else "——"],
    ]
    t2 = Table(rows2, colWidths=[26 * mm, 60 * mm, 26 * mm, 60 * mm])
    t2.setStyle(_kv_style())
    el.append(t2)

    el.append(Paragraph("三、申请说明", h2))
    el.append(Paragraph(
        f"本企业因{PURPOSE_CN.get(profile.loan_purpose.value, '经营周转')}需要,"
        f"特向贵行申请授信额度人民币 {amount} 万元,期限 {term} 个月。"
        "本企业经营状况良好,信用记录正常,具备相应还款能力,恳请贵行审批为盼。", base))
    el.append(Spacer(1, 18))
    el.append(_signature(datetime.now().strftime("%Y 年 %m 月 %d 日")))
    return el


def _form_statement(profile, result, best, theme, title, sub, h2, base, small, company, today):
    el = [_header(theme, title, sub, "企业经营情况说明书", company), Spacer(1, 6)]
    rev = profile.annual_revenue
    txt1 = (f"我单位 {company},属{profile.industry}行业,成立至今已稳定经营 "
            f"{profile.years_in_business} 年,注册资本 {profile.registered_capital} 万元,"
            f"现有员工 {profile.employees} 人。近一年实现营业额约 {rev} 万元,经营稳健,现金流良好。")
    txt2 = ("企业纳税记录" + ("规范、连续" if profile.has_tax_record else "正在完善") + ","
            "开票流水" + ("稳定" if profile.has_invoice else "持续积累中") + ","
            "征信状况" + CREDIT_CN.get(profile.credit_level.value, "良好") + ","
            + ("当前无逾期记录。" if not profile.has_overdue else "正积极处理历史逾期。"))
    txt3 = (f"本次拟向{best.provider_type if best else '银行'}申请融资 "
            f"{best.estimated_amount if best else profile.loan_amount} 万元,"
            f"主要用于{PURPOSE_CN.get(profile.loan_purpose.value, '经营周转')},"
            "预计可有效缓解资金压力、扩大经营规模、提升盈利能力。还款来源为日常经营收入,还款能力充足,风险可控。")
    el.append(Paragraph("一、企业基本情况", h2))
    el.append(Paragraph(txt1, base))
    el.append(Paragraph("二、信用与财务状况", h2))
    el.append(Paragraph(txt2, base))
    el.append(Paragraph("三、融资需求与还款安排", h2))
    el.append(Paragraph(txt3, base))
    if result.profile_highlights:
        el.append(Paragraph("四、企业优势", h2))
        for h in result.profile_highlights:
            el.append(Paragraph(f"· {h}", small))
    el.append(Spacer(1, 18))
    el.append(_signature(today))
    return el


def _form_subsidy_ledger(profile, result, theme, title, sub, h2, base, small, cell, company, today, hidden=None):
    el = [_header(theme, title, sub, "财政贴息 / 扶持政策申报台账",
                  f"{company} · {today}"), Spacer(1, 6)]
    if result.subsidies:
        rows = [["序号", "政策名称", "主管部门", "扶持内容", "申报要点", "状态"]]
        for i, s in enumerate(result.subsidies, 1):
            rows.append([str(i), Paragraph(s.name, cell), Paragraph(s.authority, cell),
                         Paragraph(s.benefit, cell), Paragraph(s.apply_points, cell), "待申报"])
        t = Table(rows, colWidths=[10 * mm, 32 * mm, 26 * mm, 42 * mm, 46 * mm, 18 * mm])
        t.setStyle(_grid_style(theme))
        el.append(t)
        el.append(Spacer(1, 8))
        el.append(Paragraph(f"共匹配 {len(result.subsidies)} 项可申报政策,"
                            "请按各主管部门要求准备材料并在窗口期内提交。", small))
    else:
        el.append(Paragraph("暂未匹配到可申报政策,建议完善纳税、参保等资质后再行申报。", base))

    if hidden:
        el.append(Spacer(1, 12))
        el.append(Paragraph("园区 / 区县独家隐藏贴息(非公开,需定向申报)", h2))
        hrows = [["序号", "政策名称", "所在地区", "最高额", "贴息", "扶持内容 / 申报路径"]]
        for i, s in enumerate(hidden, 1):
            hrows.append([str(i), Paragraph(s.get("name", ""), cell), Paragraph(s.get("region", ""), cell),
                          f"{s.get('amount_max','-')}万", f"{s.get('rate_subsidy','-')}%",
                          Paragraph(f"{s.get('benefit','')}<br/>申报:{s.get('apply_points','')}", cell)])
        ht = Table(hrows, colWidths=[10 * mm, 30 * mm, 26 * mm, 16 * mm, 14 * mm, 78 * mm])
        ht.setStyle(_grid_style(theme))
        el.append(ht)
        el.append(Spacer(1, 6))
        el.append(Paragraph(f"共解锁 {len(hidden)} 项独家隐藏贴息,名额有限,建议尽快向对应园区/区县窗口定向申报。", small))
    el.append(Spacer(1, 18))
    el.append(_signature(today))
    el.append(Spacer(1, 8))
    el.append(Paragraph("说明:本台账金额、政策为系统估算与匹配示意,最终以主管部门核定为准。",
                        ParagraphStyle("d", parent=small, fontSize=8,
                                       textColor=colors.HexColor("#9ca3af"))))
    return el
    el.append(_signature(today))
    el.append(Spacer(1, 8))
    el.append(Paragraph("说明:本台账金额、政策为系统估算与匹配示意,最终以主管部门核定为准。",
                        ParagraphStyle("d", parent=small, fontSize=8,
                                       textColor=colors.HexColor("#9ca3af"))))
    return el
