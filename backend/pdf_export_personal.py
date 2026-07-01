"""生成个人贷款方案 PDF,复用 pdf_export 的中文样式。"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table

from models import PersonalProfile, RecommendResponse
from pdf_export import _kv_style, _styles, _table_style

CREDIT_CN = {"excellent": "优秀", "good": "良好", "fair": "一般", "poor": "较差"}
OCC_CN = {
    "salaried": "上班族", "civil_servant": "公务员/事业编", "self_employed": "个体工商户",
    "freelancer": "自由职业", "professional": "专业人士", "retired": "退休", "student": "学生",
}
PURPOSE_CN = {
    "consumption": "日常消费", "decoration": "装修", "car": "购车", "education": "教育",
    "medical": "医疗", "marriage": "婚庆", "travel": "旅游", "turnover": "资金周转",
    "startup": "创业经营", "debt_optimize": "债务优化",
}


def build_personal_pdf(profile: PersonalProfile, result: RecommendResponse) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=16 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            title="个人贷款方案报告")
    base, title, sub, h2, small = _styles()
    el = []

    name = profile.name or "个人客户"
    el.append(Paragraph("个人贷款方案报告", title))
    el.append(Paragraph(f"{name} · 生成时间 {datetime.now().strftime('%Y-%m-%d %H:%M')}", sub))
    el.append(Spacer(1, 8))

    el.append(Paragraph("一、方案摘要", h2))
    el.append(Paragraph(result.summary, base))

    el.append(Paragraph("二、个人画像", h2))
    prof_rows = [
        ["职业身份", OCC_CN.get(profile.occupation_type.value, "-"), "年龄", f"{profile.age} 岁"],
        ["月收入", f"{int(profile.monthly_income)} 元", "征信状况", CREDIT_CN.get(profile.credit_level.value, "-")],
        ["社保/公积金", ("有社保" if profile.has_social_security else "无社保") + " / " + ("有公积金" if profile.has_housing_fund else "无公积金"),
         "现有月还款", f"{int(profile.monthly_debt_payment)} 元"],
        ["名下资产", ("房产 " if profile.has_house else "") + ("车辆 " if profile.has_car else "") + ("保单" if profile.has_insurance_policy else "") or "无",
         "贷款用途", PURPOSE_CN.get(profile.loan_purpose.value, "-")],
        ["贷款需求", f"{profile.loan_amount} 万元", "期望期限", f"{profile.preferred_term_months} 个月"],
    ]
    t = Table(prof_rows, colWidths=[28 * mm, 50 * mm, 28 * mm, 50 * mm])
    t.setStyle(_kv_style())
    el.append(t)

    r = result.risk
    el.append(Paragraph("三、风控评估", h2))
    el.append(Paragraph(
        f"综合评分:<b>{r.score}</b> / 100  ·  等级:<b>{r.grade}（{r.grade_label}）</b>"
        + (f"  ·  负债率:{int(r.debt_ratio*100)}%" if r.debt_ratio is not None else ""), base))
    el.append(Spacer(1, 4))
    factor_rows = [["评分因子", "影响", "说明"]]
    impact_cn = {"positive": "正向", "negative": "负向", "neutral": "中性"}
    for f in r.factors:
        factor_rows.append([f.name, impact_cn.get(f.impact, f.impact), Paragraph(f.detail, small)])
    ft = Table(factor_rows, colWidths=[26 * mm, 16 * mm, 114 * mm])
    ft.setStyle(_table_style())
    el.append(ft)

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

    if result.personalized_advice:
        el.append(Paragraph("五、个性化融资建议", h2))
        for a in result.personalized_advice:
            el.append(Paragraph(f"· {a}", small))

    if result.subsidies:
        el.append(Paragraph("六、可申报扶持政策", h2))
        srows = [["政策名称", "类别", "主管部门", "扶持内容"]]
        for s in result.subsidies:
            srows.append([Paragraph(s.name, small), s.category, s.authority, Paragraph(s.benefit, small)])
        st = Table(srows, colWidths=[34 * mm, 22 * mm, 30 * mm, 70 * mm])
        st.setStyle(_table_style())
        el.append(st)

    if result.improvement_tips:
        el.append(Paragraph("七、资质提升建议", h2))
        for tip in result.improvement_tips:
            el.append(Paragraph(f"· {tip}", small))

    el.append(Spacer(1, 12))
    el.append(Paragraph(
        "免责声明:本报告利率基准参考 LPR(一年期 3.0%、五年期以上 3.5%,2025-05-20 起),"
        "其中的额度、利率、月供及政策匹配均为基于公开规则的估算与示意,"
        "仅供参考,实际以金融机构审批结果及主管部门最新政策为准。理性借贷,量入为出。", sub))

    doc.build(el)
    buf.seek(0)
    return buf.read()
