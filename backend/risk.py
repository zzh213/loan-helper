"""风控模型:标准化、可解释的 8 维度评分卡。

评分范围 0-100,分数越高代表信用资质越好、风险越低。
每个维度独立计算「实得分 / 满分」并给出加分/扣分原因与改进建议,
明确告诉用户「为什么通过率低」。总分 = 各维度实得分之和(+行业增信附加分,封顶 100)。

该评分会反哺推荐引擎:影响可贷额度系数、利率定价与审批通过率。
"""
from typing import List, Optional

from models import EnterpriseProfile

# 行业风险系数(1.0 为基准,>1 风险更高,<1 更稳健)
INDUSTRY_RISK = {
    "制造业": 0.95,
    "批发零售": 1.05,
    "餐饮": 1.20,
    "科技": 0.90,
    "建筑": 1.15,
    "物流": 1.00,
    "农业": 1.10,
    "服务业": 1.00,
    "医疗健康": 0.90,
    "教育培训": 1.10,
    "文化旅游": 1.15,
    "电商直播": 1.05,
    "美容美发": 1.10,
    "五金机电": 1.00,
}

# 8 个标准维度的满分权重(合计 100)
DIM_MAX = {
    "credit": 24,       # 征信状况(含当前逾期)
    "revenue": 15,      # 营收规模
    "years": 12,        # 经营年限
    "tax": 12,          # 纳税信用
    "collateral": 12,   # 抵押物
    "orders": 9,        # 订单 / 开票流水
    "debt": 10,         # 负债杠杆
    "industry": 6,      # 行业风险
}

DIM_ORDER = ["credit", "revenue", "years", "tax", "collateral", "orders", "debt", "industry"]
DIM_NAME = {
    "credit": "征信状况",
    "revenue": "营收规模",
    "years": "经营年限",
    "tax": "纳税信用",
    "collateral": "抵押物",
    "orders": "订单/流水",
    "debt": "负债杠杆",
    "industry": "行业风险",
}


def credit_label(v: str) -> str:
    return {"excellent": "优秀", "good": "良好", "fair": "一般", "poor": "较差"}.get(v, "未知")


def _debt_ratio(profile: EnterpriseProfile) -> Optional[float]:
    """估算负债率 = 期望贷款额 / 年营业额。仅作粗略参考。"""
    if profile.annual_revenue <= 0:
        return None
    return round(profile.loan_amount / profile.annual_revenue, 2)


def _level(earned: float, mx: float) -> str:
    """维度表现等级:good / mid / weak。"""
    if mx <= 0:
        return "mid"
    r = earned / mx
    if r >= 0.75:
        return "good"
    if r >= 0.45:
        return "mid"
    return "weak"


def _score_credit(p: EnterpriseProfile):
    mx = DIM_MAX["credit"]
    base = {"excellent": 24, "good": 20, "fair": 13, "poor": 7}.get(p.credit_level.value, 12)
    earned = base
    reason = f"征信等级{credit_label(p.credit_level.value)}"
    advice = ""
    if p.has_overdue:
        earned -= 10
        reason += ",且当前存在逾期(重度扣分)"
        advice = "优先结清逾期,保持后续 6-24 个月零逾期,是提升通过率最快的方式。"
    elif p.credit_level.value in ("fair", "poor"):
        advice = "养征信:减少硬查询、按时还款,6 个月后等级上调可显著提额降息。"
    else:
        reason += ",无当前逾期,信用表现稳定"
    earned = max(0, min(mx, earned))
    return earned, reason, advice


def _score_revenue(p: EnterpriseProfile):
    r = p.annual_revenue
    if r >= 1000:
        return 15, f"年营收 {r} 万,规模大、还款来源充足", ""
    if r >= 500:
        return 13, f"年营收 {r} 万,规模较好", ""
    if r >= 200:
        return 10, f"年营收 {r} 万,规模中等", "稳定并提升开票营收,可解锁更高额度产品。"
    if r >= 50:
        return 6, f"年营收 {r} 万,规模偏小,额度受限", "做大真实经营流水,营收过 100 万后可申产品明显增多。"
    return 2, f"年营收 {r} 万,规模过小,多数产品准入受限", "先积累经营流水与营收,达到 50 万门槛再申请更稳。"


def _score_years(p: EnterpriseProfile):
    y = p.years_in_business
    if y >= 3:
        return 12, f"经营 {y} 年,持续经营能力强", ""
    if y >= 2:
        return 9, f"经营 {y} 年,已跨过 2 年门槛", ""
    if y >= 1:
        return 6, f"经营 {y} 年,处于成长期", "经营满 2 年后通过率明显提升,可择机再申。"
    return 2, f"经营 {y} 年,初创企业风险偏高", "多数银行要求经营满 1-2 年,可先选互联网银行流水贷过渡。"


def _score_tax(p: EnterpriseProfile):
    if p.has_tax_record:
        return 12, "有连续纳税记录,可解锁银税类低息产品", ""
    return 3, "缺少连续纳税记录,银税类低息产品受限", "补齐连续纳税(纳税信用 B 级以上),可解锁银税互动贷。"


def _score_collateral(p: EnterpriseProfile):
    if p.has_collateral and p.collateral_value > 0:
        cover = p.collateral_value / max(1.0, p.loan_amount)
        if cover >= 1.2:
            return 12, f"抵押物估值 {p.collateral_value} 万,足额覆盖需求,可显著增信", ""
        if cover >= 0.6:
            return 9, f"抵押物估值 {p.collateral_value} 万,可部分增信", ""
        return 6, f"抵押物估值 {p.collateral_value} 万,覆盖不足,仍以信用为主", ""
    return 3, "暂无抵押物,以信用资质为主", "如有房产/设备可作抵押,能大幅提额降息;无抵押可走政府性融资担保补足。"


def _score_orders(p: EnterpriseProfile):
    if p.has_invoice:
        return 9, "有稳定开票流水/订单,经营真实性强", ""
    return 3, "缺少稳定开票流水/订单佐证", "保持 6 个月以上稳定开票或对公流水,直接提高授信额度。"


def _score_debt(p: EnterpriseProfile):
    dr = _debt_ratio(p)
    if dr is None:
        return 5, "无营收数据,负债杠杆无法评估", "补充真实年营收后可精确评估杠杆。", dr
    pct = int(dr * 100)
    if dr <= 0.3:
        return 10, f"贷款需求约为年营收的 {pct}%,杠杆稳健", "", dr
    if dr <= 0.6:
        return 7, f"贷款需求约为年营收的 {pct}%,杠杆适中", "", dr
    if dr <= 1.0:
        return 3, f"贷款需求达年营收的 {pct}%,杠杆偏高", "把首次申请额度下调至年营收 60% 以内,通过率更高。", dr
    return 0, f"贷款需求达年营收的 {pct}%,杠杆过高,极易被拒", "强烈建议下调额度或分笔申请,当前额度大概率被压降。", dr


def _score_industry(p: EnterpriseProfile):
    coef = INDUSTRY_RISK.get(p.industry, 1.0)
    if coef <= 0.95:
        return 6, f"{p.industry}行业风险较低,银行偏好度高", "", coef
    if coef >= 1.10:
        return 2, f"{p.industry}行业波动性较高,风控相对审慎", "波动行业可强化抵押/纳税/订单佐证来对冲行业扣分。", coef
    return 4, f"{p.industry}行业风险适中", "", coef


def assess(profile: EnterpriseProfile) -> dict:
    """返回风险评估结果字典(含标准化 8 维评分卡)。"""
    scorecard = []

    e, reason, advice = _score_credit(profile)
    scorecard.append(("credit", e, reason, advice))
    e, reason, advice = _score_revenue(profile)
    scorecard.append(("revenue", e, reason, advice))
    e, reason, advice = _score_years(profile)
    scorecard.append(("years", e, reason, advice))
    e, reason, advice = _score_tax(profile)
    scorecard.append(("tax", e, reason, advice))
    e, reason, advice = _score_collateral(profile)
    scorecard.append(("collateral", e, reason, advice))
    e, reason, advice = _score_orders(profile)
    scorecard.append(("orders", e, reason, advice))
    de, dreason, dadvice, dr = _score_debt(profile)
    scorecard.append(("debt", de, dreason, dadvice))
    ie, ireason, iadvice, coef = _score_industry(profile)
    scorecard.append(("industry", ie, ireason, iadvice))

    base_score = sum(item[1] for item in scorecard)

    # 行业专属增信项(垂直模板加分):每命中一项 +3,最高 +10(附加分,不占 8 维满分)
    bonus_hit = [b for b in (profile.industry_bonus or []) if b]
    bonus_add = min(10, len(bonus_hit) * 3) if bonus_hit else 0

    score = max(5, min(100, round(base_score + bonus_add)))

    # 组装维度明细
    dims = []
    for key, earned, reason, advice in scorecard:
        mx = DIM_MAX[key]
        dims.append({
            "key": key,
            "name": DIM_NAME[key],
            "score": round(earned),
            "max": mx,
            "level": _level(earned, mx),   # good / mid / weak
            "reason": reason,
            "advice": advice,
        })

    # 「为什么通过率低」:挑出失分最多的薄弱维度(实得 < 60% 满分)
    weak_points = []
    for d in sorted(dims, key=lambda x: (x["score"] / x["max"]) if x["max"] else 1):
        if d["max"] and d["score"] / d["max"] < 0.6:
            weak_points.append({
                "name": d["name"],
                "lost": round(d["max"] - d["score"]),
                "reason": d["reason"],
                "advice": d["advice"] or "针对性补强该项材料可提升通过率。",
            })
        if len(weak_points) >= 4:
            break

    # 兼容旧结构:factors(name/impact/detail)
    impact_map = {"good": "positive", "mid": "neutral", "weak": "negative"}
    factors = [{"name": d["name"], "impact": impact_map[d["level"]], "detail": d["reason"]} for d in dims]
    if bonus_add:
        factors.append({"name": "行业增信", "impact": "positive",
                        "detail": f"具备 {profile.industry} 专属加分项:{'、'.join(bonus_hit[:4])}(+{bonus_add}分)"})

    if score >= 85:
        grade, grade_label = "A", "优质低风险"
    elif score >= 70:
        grade, grade_label = "B", "良好可控"
    elif score >= 55:
        grade, grade_label = "C", "中等风险"
    elif score >= 40:
        grade, grade_label = "D", "较高风险"
    else:
        grade, grade_label = "E", "高风险"

    return {
        "score": score,
        "grade": grade,
        "grade_label": grade_label,
        "debt_ratio": dr,
        "industry_coefficient": coef,
        "scorecard": dims,
        "bonus_add": bonus_add,
        "weak_points": weak_points,
        "factors": factors,
    }


def amount_multiplier(score: int) -> float:
    """风险评分对可贷额度的整体调节系数。"""
    if score >= 85:
        return 1.15
    if score >= 70:
        return 1.0
    if score >= 55:
        return 0.85
    if score >= 40:
        return 0.7
    return 0.55


def rate_adjustment(score: int) -> float:
    """风险评分对利率的调整(百分点)。分高减息,分低加息。"""
    if score >= 85:
        return -0.5
    if score >= 70:
        return 0.0
    if score >= 55:
        return 0.6
    if score >= 40:
        return 1.5
    return 3.0
