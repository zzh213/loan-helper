"""风控模型:基于企业多维度信息计算风险评分、等级与因子明细。

评分范围 0-100,分数越高代表信用资质越好、风险越低。
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

CREDIT_BASE = {"excellent": 95, "good": 82, "fair": 65, "poor": 45}


class RiskFactor:
    def __init__(self, name: str, impact: str, detail: str):
        self.name = name        # 因子名称
        self.impact = impact    # positive / negative / neutral
        self.detail = detail    # 说明


def _debt_ratio(profile: EnterpriseProfile) -> Optional[float]:
    """估算负债率 = 期望贷款额 / 年营业额。仅作粗略参考。"""
    if profile.annual_revenue <= 0:
        return None
    return round(profile.loan_amount / profile.annual_revenue, 2)


def assess(profile: EnterpriseProfile) -> dict:
    """返回风险评估结果字典。"""
    factors: List[RiskFactor] = []
    score = float(CREDIT_BASE.get(profile.credit_level.value, 60))

    # 1. 征信(基准已体现)
    if profile.credit_level.value in ("excellent", "good"):
        factors.append(RiskFactor("征信状况", "positive",
                                   "征信记录良好,是审批与定价的核心加分项"))
    else:
        factors.append(RiskFactor("征信状况", "negative",
                                   "征信等级偏低,会压低额度并抬高利率"))

    # 2. 当前逾期
    if profile.has_overdue:
        score -= 18
        factors.append(RiskFactor("当前逾期", "negative",
                                   "存在当前逾期,严重影响审批,建议优先结清"))
    else:
        factors.append(RiskFactor("当前逾期", "positive", "无当前逾期,信用表现稳定"))

    # 3. 经营年限
    if profile.years_in_business >= 3:
        score += 8
        factors.append(RiskFactor("经营稳定性", "positive",
                                   f"经营 {profile.years_in_business} 年,持续经营能力强"))
    elif profile.years_in_business >= 1:
        score += 2
        factors.append(RiskFactor("经营稳定性", "neutral",
                                   f"经营 {profile.years_in_business} 年,处于成长期"))
    else:
        score -= 8
        factors.append(RiskFactor("经营稳定性", "negative",
                                   "经营不足 1 年,初创企业风险偏高"))

    # 4. 营收规模
    if profile.annual_revenue >= 500:
        score += 8
        factors.append(RiskFactor("营收规模", "positive", "营收规模较大,还款来源充足"))
    elif profile.annual_revenue >= 100:
        score += 4
        factors.append(RiskFactor("营收规模", "positive", "营收规模中等,具备一定还款能力"))
    elif profile.annual_revenue >= 30:
        factors.append(RiskFactor("营收规模", "neutral", "营收规模较小,额度受限"))
    else:
        score -= 6
        factors.append(RiskFactor("营收规模", "negative", "营收规模偏小,可贷额度有限"))

    # 5. 负债率 / 杠杆
    dr = _debt_ratio(profile)
    if dr is not None:
        if dr <= 0.3:
            score += 6
            factors.append(RiskFactor("负债杠杆", "positive",
                                      f"贷款需求约为年营收的 {int(dr*100)}%,杠杆稳健"))
        elif dr <= 0.6:
            factors.append(RiskFactor("负债杠杆", "neutral",
                                      f"贷款需求约为年营收的 {int(dr*100)}%,杠杆适中"))
        else:
            score -= 10
            factors.append(RiskFactor("负债杠杆", "negative",
                                      f"贷款需求达年营收的 {int(dr*100)}%,杠杆偏高,建议下调额度或分期申请"))

    # 6. 抵押物
    if profile.has_collateral and profile.collateral_value > 0:
        score += 7
        factors.append(RiskFactor("抵押担保", "positive",
                                   f"有抵押物(估值 {profile.collateral_value} 万元),可显著增信"))
    else:
        factors.append(RiskFactor("抵押担保", "neutral", "暂无抵押物,以信用资质为主"))

    # 7. 纳税 / 开票
    if profile.has_tax_record:
        score += 6
        factors.append(RiskFactor("纳税信用", "positive", "有连续纳税记录,可解锁银税类低息产品"))
    if profile.has_invoice:
        score += 3
        factors.append(RiskFactor("经营流水", "positive", "有稳定开票流水,经营真实性强"))
    if not profile.has_tax_record and not profile.has_invoice:
        score -= 4
        factors.append(RiskFactor("经营凭证", "negative",
                                   "缺少纳税与开票凭证,信用评估依据不足"))

    # 8. 行业风险
    ind_coef = INDUSTRY_RISK.get(profile.industry, 1.0)
    if ind_coef <= 0.95:
        score += 4
        factors.append(RiskFactor("行业风险", "positive",
                                   f"{profile.industry}行业风险较低,银行偏好度高"))
    elif ind_coef >= 1.10:
        score -= 5
        factors.append(RiskFactor("行业风险", "negative",
                                   f"{profile.industry}行业波动性较高,风控相对审慎"))
    else:
        factors.append(RiskFactor("行业风险", "neutral", f"{profile.industry}行业风险适中"))

    # 9. 行业专属增信项(垂直模板加分):每命中一项 +3,最高 +12
    bonus_hit = [b for b in (profile.industry_bonus or []) if b]
    if bonus_hit:
        add = min(12, len(bonus_hit) * 3)
        score += add
        factors.append(RiskFactor("行业增信", "positive",
                                   f"具备 {profile.industry} 专属加分项:{'、'.join(bonus_hit[:4])}(+{add}分)"))

    score = max(5, min(100, round(score)))

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
        "industry_coefficient": ind_coef,
        "factors": [{"name": f.name, "impact": f.impact, "detail": f.detail} for f in factors],
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
