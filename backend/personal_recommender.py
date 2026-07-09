"""个人贷款推荐引擎。

复用企业端的 RecommendResponse / RecommendedPlan / RiskAssessment 结构,
使前端渲染逻辑完全共用;金额单位:万元,收入单位:元/月。
"""
from typing import List, Tuple

from models import (PersonalProfile, PlanTier, RecommendedPlan,
                    RecommendResponse, RiskAssessment, RiskFactorModel)
from personal_products import INCOME_TYPE_FACTOR, PERSONAL_PRODUCTS
from personal_policies import match_personal_policies
from products import CREDIT_RANK
from plain_language import build_plain_language

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


def _monthly_payment(principal_wan: float, annual_rate_pct: float, months: int) -> float:
    if months <= 0:
        return 0.0
    r = annual_rate_pct / 100 / 12
    if r == 0:
        return round(principal_wan / months, 2)
    factor = (r * (1 + r) ** months) / ((1 + r) ** months - 1)
    return round(principal_wan * factor, 2)


def _dti(p: PersonalProfile) -> float:
    if p.monthly_income <= 0:
        return 1.0
    return round(p.monthly_debt_payment / p.monthly_income, 2)


def assess_personal(p: PersonalProfile) -> dict:
    """个人综合风控评分,返回与企业端一致的结构。"""
    score = 60
    factors: List[dict] = []

    def add(name, impact, detail):
        factors.append({"name": name, "impact": impact, "detail": detail})

    inc = p.monthly_income
    if inc >= 15000:
        score += 12; add("收入水平", "positive", f"月收入 {int(inc)} 元,还款能力强")
    elif inc >= 8000:
        score += 8; add("收入水平", "positive", f"月收入 {int(inc)} 元,较为充足")
    elif inc >= 5000:
        score += 4; add("收入水平", "neutral", f"月收入 {int(inc)} 元,中等水平")
    elif inc >= 3000:
        add("收入水平", "neutral", f"月收入 {int(inc)} 元,偏低")
    else:
        score -= 8; add("收入水平", "negative", "月收入较低,可贷额度受限")

    it = p.income_type
    if it == "salary":
        score += 6; add("收入形式", "positive", "打卡工资,收入可核验,银行认可度高")
    elif it == "business":
        score += 2; add("收入形式", "neutral", "经营性收入,建议留存流水凭证")
    else:
        score -= 2; add("收入形式", "negative", "现金/混合收入不易核验,建议转银行代发")

    if p.has_social_security:
        score += 5; add("社保", "positive", "连续缴纳社保,身份与稳定性加分")
    if p.has_housing_fund:
        score += 6; add("公积金", "positive", "连续缴存公积金,可申请利率较优的公积金贷")

    if p.work_years >= 3:
        score += 6; add("职业稳定性", "positive", f"当前职业 {p.work_years} 年,稳定性好")
    elif p.work_years >= 1:
        score += 3
    elif p.work_years < 0.5:
        score -= 4; add("职业稳定性", "negative", "工作/经营时间较短,银行偏谨慎")

    cb = {"excellent": 14, "good": 8, "fair": 0, "poor": -12}
    score += cb.get(p.credit_level.value, 0)
    add("个人征信", "positive" if cb.get(p.credit_level.value, 0) >= 8 else
        ("negative" if cb.get(p.credit_level.value, 0) < 0 else "neutral"),
        f"征信{CREDIT_CN.get(p.credit_level.value, '')}," +
        ("是申请利率较优产品的敲门砖" if p.credit_level.value in ("excellent", "good") else "会影响额度与利率,建议先修复"))

    if p.has_overdue:
        score -= 12; add("当前逾期", "negative", "存在逾期会显著影响审批,建议先结清")

    dti = _dti(p)
    if dti > 0.7:
        score -= 12; add("负债率", "negative", f"月还款/月收入约 {int(dti*100)}%,偏高,易被拒")
    elif dti > 0.5:
        score -= 6; add("负债率", "negative", f"月还款占比约 {int(dti*100)}%,偏高")
    elif dti <= 0.3:
        score += 4; add("负债率", "positive", f"月还款占比约 {int(dti*100)}%,负债健康")

    if p.has_house:
        score += 8; add("资产", "positive", "名下有房,可办大额房抵贷(利率相对较优)")
    if p.has_car:
        score += 3
    if p.has_insurance_policy:
        score += 2

    occ = p.occupation_type.value
    if occ in ("civil_servant", "professional"):
        score += 8; add("职业属性", "positive", "职业稳定,是银行最青睐的优质客群")
    elif occ == "salaried":
        score += 4
    elif occ == "self_employed":
        score += 2
    elif occ == "freelancer":
        score -= 2; add("职业属性", "neutral", "自由职业建议补充稳定流水与社保")
    elif occ == "student":
        score -= 6; add("职业属性", "negative", "学生无稳定收入,建议由父母作为共同还款人")

    if 25 <= p.age <= 55:
        score += 2
    elif p.age > 65:
        score -= 4; add("年龄", "negative", "年龄偏大,期限与额度可能受限")
    elif p.age < 22:
        score -= 3

    score = max(0, min(100, score))
    if score >= 80:
        grade, label = "A", "优质"
    elif score >= 65:
        grade, label = "B", "良好"
    elif score >= 50:
        grade, label = "C", "中等"
    else:
        grade, label = "D", "需关注"

    return {
        "score": score, "grade": grade, "grade_label": label,
        "debt_ratio": dti, "industry_coefficient": 1.0, "factors": factors,
    }


def _amount_multiplier(score: int) -> float:
    if score >= 80:
        return 1.15
    if score >= 65:
        return 1.0
    if score >= 50:
        return 0.85
    return 0.7


def _rate_adjustment(score: int) -> float:
    if score >= 80:
        return -0.6
    if score >= 65:
        return 0.0
    if score >= 50:
        return 0.8
    return 1.8


def _eligible(prod: dict, p: PersonalProfile) -> Tuple[bool, List[str]]:
    reasons = []
    if p.monthly_income < prod.get("min_income", 0):
        reasons.append(f"月收入需≥{int(prod['min_income'])}元")
    if CREDIT_RANK[p.credit_level.value] < CREDIT_RANK[prod["min_credit"]]:
        reasons.append("征信等级不满足")
    if p.work_years < prod.get("min_work_years", 0):
        reasons.append("在职/经营时间不足")
    if prod.get("need_salary_card") and p.income_type != "salary":
        reasons.append("需银行代发打卡工资")
    if prod.get("need_social_security") and not p.has_social_security:
        reasons.append("需连续缴纳社保")
    if prod.get("need_housing_fund") and not p.has_housing_fund:
        reasons.append("需连续缴存公积金")
    if prod.get("need_house") and not p.has_house:
        reasons.append("需名下有房产")
    if prod.get("need_car") and not p.has_car:
        reasons.append("需名下有车辆")
    if prod.get("need_insurance") and not p.has_insurance_policy:
        reasons.append("需持有寿险/年金保单")
    if prod.get("need_entrepreneur") and not (p.is_entrepreneur or p.loan_purpose.value == "startup"):
        reasons.append("需在创业或经营个体工商户")
    if prod.get("need_occupation") and p.occupation_type.value not in prod["need_occupation"]:
        reasons.append("仅限特定职业身份")
    if prod.get("fit_purposes") and p.loan_purpose.value not in prod["fit_purposes"]:
        reasons.append("与所选用途不匹配")
    return (len(reasons) == 0, reasons)


def _estimate_amount(prod: dict, p: PersonalProfile, risk_mult: float) -> float:
    amounts = [0.0]
    itf = INCOME_TYPE_FACTOR.get(p.income_type, 0.85)
    if prod.get("income_multiple"):
        amounts.append(p.monthly_income * prod["income_multiple"] / 10000 * itf)
    if prod.get("fund_multiple") and p.housing_fund_monthly > 0:
        amounts.append(p.housing_fund_monthly * prod["fund_multiple"] / 10000)
    if prod.get("need_house") and p.house_value > 0:
        amounts.append(p.house_value * prod.get("collateral_ratio", 0.7))
    if prod.get("need_car") and p.car_value > 0:
        amounts.append(p.car_value * prod.get("collateral_ratio", 0.8))
    if prod.get("need_insurance"):
        amounts.append(prod["max_amount"] * 0.6)
    if prod.get("need_entrepreneur"):
        amounts.append(prod["max_amount"])
    amount = max(amounts)

    credit_bonus = {"excellent": 1.15, "good": 1.0, "fair": 0.85, "poor": 0.7}
    amount *= credit_bonus.get(p.credit_level.value, 1.0)
    amount *= risk_mult
    amount = min(amount, prod["max_amount"])
    amount = min(amount, max(p.loan_amount, amount))
    return round(amount, 1)


def _score(prod: dict, p: PersonalProfile, est: float, rate: float) -> Tuple[int, List[str]]:
    score = 50
    reasons = []
    if est >= p.loan_amount:
        score += 20
        reasons.append(f"预估额度 {est} 万元可满足你 {p.loan_amount} 万元的需求")
    else:
        ratio = est / p.loan_amount if p.loan_amount else 0
        score += int(20 * ratio)
        reasons.append(f"预估额度约 {est} 万元,约为需求的 {int(ratio*100)}%")

    if rate <= 5:
        score += 20; reasons.append(f"年化低至 {rate}%,资金成本很低")
    elif rate <= 8:
        score += 12; reasons.append(f"年化约 {rate}%,成本适中")
    elif rate <= 15:
        score += 4
    else:
        score -= 8; reasons.append("利率偏高,建议仅作短期周转")

    cb = {"excellent": 12, "good": 8, "fair": 3, "poor": -5}
    score += cb.get(p.credit_level.value, 0)

    if p.urgent and ("实时" in prod["release_days"] or "当天" in prod["release_days"]):
        score += 10
        reasons.append(f"放款快({prod['release_days']}),契合你的急用需求")

    if prod["provider_type"] == "政策性/贴息":
        score += 8
        reasons.append("享受政府贴息,综合成本最优")

    reasons.append(prod["highlights"])
    return (max(0, min(100, score)), reasons)


def _approval_prob(score: int) -> str:
    if score >= 80:
        return "很高"
    if score >= 65:
        return "较高"
    if score >= 50:
        return "中等"
    return "偏低"


def _cautions(prod: dict, p: PersonalProfile, rate: float) -> List[str]:
    c = []
    if rate >= 15:
        c.append("利率较高,务必算清总还款额,避免长期使用与以贷养贷")
    if prod.get("requires_collateral"):
        c.append("需办理抵押/质押,放款周期相对较长")
    if p.has_overdue:
        c.append("当前逾期会影响审批与额度,建议先结清征信")
    if p.preferred_term_months > prod["max_term_months"]:
        c.append(f"该产品最长 {prod['max_term_months']} 个月,短于你期望的 {p.preferred_term_months} 个月")
    return c


def _improvement_tips(p: PersonalProfile) -> List[str]:
    tips = []
    if p.credit_level.value in ("fair", "poor"):
        tips.append("按时还款、降低信用卡使用率,征信修复后额度与利率会明显改善")
    if p.has_overdue:
        tips.append("优先结清当前逾期,征信恢复后再申请银行利率较优的产品")
    if p.income_type != "salary":
        tips.append("尽量将收入转为银行代发工资,或沉淀稳定流水,可大幅提升可贷额度")
    if not p.has_social_security:
        tips.append("连续缴纳社保能提升稳定性评分,是很多银行信用贷的隐性门槛")
    if not p.has_housing_fund:
        tips.append("如有条件缴存公积金,可解锁利率更低的公积金信用贷")
    if _dti(p) > 0.5:
        tips.append("现有负债偏高,建议先偿还部分小额高息负债,降低负债率后再申请")
    if not (p.has_house or p.has_car or p.has_insurance_policy):
        tips.append("如有房/车/保单等资产,可申请额度更高、利率更低的抵押质押类产品")
    return tips


def _advice(p: PersonalProfile, risk: dict, plans: List[RecommendedPlan]) -> List[str]:
    advice = []
    grade = risk["grade"]
    if grade in ("A", "B"):
        advice.append(f"你的综合评分 {risk['score']} 分(等级 {grade}·{risk['grade_label']}),"
                      "资质优良,建议优先选择银行利率较优的信用贷,并可争取更高额度与更长期限。")
    elif grade == "C":
        advice.append(f"综合评分 {risk['score']} 分(等级 {grade}·{risk['grade_label']}),"
                      "建议先选审批友好的产品,控制单笔额度,按时还款积累信用后再升级。")
    else:
        advice.append(f"综合评分 {risk['score']} 分(等级 {grade}·{risk['grade_label']}),"
                      "当前获批优质产品较难,建议先小额短期周转、避免多头借贷,修复资质后再申请。")

    dti = risk.get("debt_ratio")
    if dti is not None and dti > 0.5:
        safe = round(max(0, (p.monthly_income * 0.5 - p.monthly_debt_payment)) * p.preferred_term_months / 10000, 1)
        advice.append(f"按月收入的 50% 作为还款上限,你每月可承受的新增月供约 "
                      f"{int(max(0, p.monthly_income*0.5 - p.monthly_debt_payment))} 元,"
                      + (f"对应本次期限下建议额度控制在 {safe} 万元以内。" if safe > 0 else "建议先降负债再借款。"))

    pm = {
        "consumption": "日常消费建议用随借随还的信用贷,按实际用款计息更省。",
        "decoration": "装修可对比家装分期与普通信用贷,哪个折算年化更低选哪个,并留意银行贴息活动。",
        "car": "购车优先比较厂商金融贴息方案与银行车贷,免息期活动往往比现金贷更划算。",
        "education": "教育用途可先申请国家助学贷款/贴息政策,不足部分再用利率较优的信用贷补充。",
        "medical": "医疗建议先走医保报销与大病救助,减少举债金额后再申请贷款。",
        "marriage": "婚庆属一次性支出,建议控制额度、选短期限,避免婚后长期背高息。",
        "turnover": "短期周转优先选随借随还产品,回款后尽快结清以省利息。",
        "startup": "创业务必先申请'创业担保贷'政府贴息,这是成本最低的资金,再考虑其他补充。",
        "debt_optimize": "以低息置换高息(如用银行贷结清网贷)可省利息,但切忌越借越多。",
        "travel": "旅游为弹性消费,建议量入为出、选小额短期,避免为非必需支出长期负债。",
    }
    advice.append(pm.get(p.loan_purpose.value, ""))

    if p.urgent and plans:
        fast = [pl for pl in plans if "实时" in pl.expected_release_days or "当天" in pl.expected_release_days]
        if fast:
            advice.append(f"你标注了急需放款,【{fast[0].product_name}】放款最快({fast[0].expected_release_days}),可优先对接。")

    return [a for a in advice if a]


def _build_tiers(plans: List[RecommendedPlan], has_subsidy: bool) -> List[dict]:
    if not plans:
        return []
    tiers = []

    steady_pool = [p for p in plans
                   if p.provider_type != "持牌消费金融"
                   and (p.annual_rate_min + p.annual_rate_max) / 2 <= 12] or plans
    steady = max(steady_pool, key=lambda p: (p.local_approval_rate, p.score))
    tiers.append({
        "key": "steady", "name": "稳健审批版", "tagline": "偏重审批稳妥",
        "product_id": steady.product_id, "product_name": steady.product_name,
        "headline": f"通过率{steady.approval_probability} · 参考通过率 {steady.local_approval_rate}%",
        "reason": f"该产品门槛友好、通过率约 {steady.local_approval_rate}%,预估额度 {steady.estimated_amount} 万元,适合稳妥拿下放款。",
        "risk_note": steady.cautions[0] if steady.cautions else "整体风险较低",
    })

    sprint = max(plans, key=lambda p: (p.estimated_amount, p.score))
    tiers.append({
        "key": "sprint", "name": "额度优先版", "tagline": "偏重更高授信额度",
        "product_id": sprint.product_id, "product_name": sprint.product_name,
        "headline": f"最高额度 {sprint.estimated_amount} 万元 · 年化 {sprint.annual_rate_min}%-{sprint.annual_rate_max}%",
        "reason": f"该产品可冲刺最高 {sprint.estimated_amount} 万元,适合大额需求,但审批相对严格。",
        "risk_note": (sprint.hidden_criteria or "审批门槛较高,需备齐材料")
                     + ("。当前需抵押,放款偏慢" if sprint.requires_collateral else ""),
    })

    def cost_key(p):
        return (0 if p.subsidy_linked else 1, (p.annual_rate_min + p.annual_rate_max) / 2)
    cheap = min(plans, key=cost_key)
    tiers.append({
        "key": "subsidy", "name": "利率优选版", "tagline": "资金成本较优",
        "product_id": cheap.product_id, "product_name": cheap.product_name,
        "headline": f"综合年化 {cheap.annual_rate_min}%-{cheap.annual_rate_max}%"
                    + (" · 含政府贴息" if cheap.subsidy_linked else ""),
        "reason": f"该产品年化最低({cheap.annual_rate_min}%-{cheap.annual_rate_max}%),"
                  + ("叠加政府贴息后成本几乎最低。" if cheap.subsidy_linked else "资金成本最优。"),
        "risk_note": cheap.cautions[0] if cheap.cautions else "需满足产品准入条件",
    })
    return tiers


def recommend_personal(p: PersonalProfile) -> RecommendResponse:
    risk = assess_personal(p)
    risk_mult = _amount_multiplier(risk["score"])
    rate_adj = _rate_adjustment(risk["score"])

    plans: List[RecommendedPlan] = []
    for prod in PERSONAL_PRODUCTS:
        ok, _ = _eligible(prod, p)
        if not ok:
            continue
        est = _estimate_amount(prod, p, risk_mult)
        if est <= 0:
            continue
        term = min(p.preferred_term_months, prod["max_term_months"])
        span = prod["annual_rate_max"] - prod["annual_rate_min"]
        pos = {"excellent": 0.0, "good": 0.3, "fair": 0.6, "poor": 0.9}
        rate = prod["annual_rate_min"] + span * pos.get(p.credit_level.value, 0.5) + rate_adj
        rate = round(max(prod["annual_rate_min"], min(prod["annual_rate_max"], rate)), 2)

        score, match_reasons = _score(prod, p, est, rate)
        monthly = _monthly_payment(est, rate, term)
        total_interest = round(monthly * term - est, 2)

        plans.append(RecommendedPlan(
            product_id=prod["id"], product_name=prod["name"],
            provider_type=prod["provider_type"], score=score,
            approval_probability=_approval_prob(score), estimated_amount=est,
            annual_rate_min=prod["annual_rate_min"], annual_rate_max=prod["annual_rate_max"],
            suggested_term_months=term, monthly_payment_estimate=monthly,
            total_interest_estimate=max(0.0, total_interest),
            requires_collateral=prod.get("requires_collateral", False),
            expected_release_days=prod["release_days"], match_reasons=match_reasons,
            cautions=_cautions(prod, p, rate), hidden_criteria=prod.get("hidden_criteria", ""),
            local_approval_rate=prod.get("local_approval_rate", 0),
            subsidy_linked=prod.get("subsidy_linked", False),
        ))

    plans.sort(key=lambda x: x.score, reverse=True)

    highlights = [
        f"身份:{OCC_CN.get(p.occupation_type.value, '')}"
        + (f" · {p.occupation_detail}" if p.occupation_detail else "")
        + f" | 年龄 {p.age} 岁 | 月收入 {int(p.monthly_income)} 元",
        f"征信:{CREDIT_CN.get(p.credit_level.value, '')}"
        + (" | 有社保" if p.has_social_security else "")
        + (" | 有公积金" if p.has_housing_fund else "")
        + (" | 有房" if p.has_house else "")
        + (" | 有车" if p.has_car else ""),
        f"需求:{p.loan_amount} 万元 / {p.preferred_term_months} 个月 · 用途{PURPOSE_CN.get(p.loan_purpose.value, '')}"
        + (" | 急需放款" if p.urgent else ""),
    ]

    subsidies = match_personal_policies(p)
    advice = _advice(p, risk, plans)
    tiers = [PlanTier(**t) for t in _build_tiers(plans, bool(subsidies))]

    if plans:
        best = plans[0]
        summary = (
            f"为你匹配到 {len(plans)} 个可申请方案,最优推荐【{best.product_name}】:"
            f"预估额度 {best.estimated_amount} 万元,年化 {best.annual_rate_min}%-{best.annual_rate_max}%,"
            f"通过率{best.approval_probability},{best.expected_release_days}放款。"
            f"综合评分 {risk['score']} 分(等级 {risk['grade']})。"
            + (f"另为你匹配到 {len(subsidies)} 项可申报的扶持政策。" if subsidies else "")
        )
    else:
        summary = (
            "根据当前资质暂未匹配到合适产品,通常是收入、征信或负债率未达门槛。"
            "请参考下方优化建议提升资质后再申请。"
            + (f"同时为你匹配到 {len(subsidies)} 项可申报的扶持政策。" if subsidies else "")
        )

    return RecommendResponse(
        summary=summary,
        profile_highlights=highlights,
        risk=RiskAssessment(**risk),
        improvement_tips=_improvement_tips(p),
        personalized_advice=advice,
        subsidies=subsidies,
        plans=plans,
        tiers=tiers,
        guarantee=None,
        plain_language=build_plain_language(
            plans=plans, risk=risk, subsidies=subsidies,
            requested_amount=p.loan_amount, is_personal=True,
        ),
    )
