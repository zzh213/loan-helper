"""推荐引擎:根据企业实际情况匹配产品并打分排序。"""
from typing import List

from models import (EnterpriseProfile, PlanTier, RecommendedPlan,
                    RecommendResponse, RiskAssessment)
from products import CREDIT_RANK, PRODUCTS
from risk import amount_multiplier, assess, rate_adjustment
from subsidies import match_policies
from guarantee import build_guarantee
from plain_language import build_plain_language
import storage


def _monthly_payment(principal_wan: float, annual_rate_pct: float, months: int) -> float:
    """等额本息月供估算,返回单位:万元。"""
    if months <= 0:
        return 0.0
    r = annual_rate_pct / 100 / 12
    if r == 0:
        return round(principal_wan / months, 2)
    factor = (r * (1 + r) ** months) / ((1 + r) ** months - 1)
    return round(principal_wan * factor, 2)


def _eligible(p: dict, profile: EnterpriseProfile) -> (bool, List[str]):
    """硬性准入判断,返回 (是否通过, 不通过原因列表)。"""
    reasons = []
    if profile.years_in_business < p["min_years"]:
        reasons.append(f"经营年限不足({p['min_years']}年起)")
    if profile.annual_revenue < p["min_annual_revenue"]:
        reasons.append(f"年营业额需≥{p['min_annual_revenue']}万元")
    if CREDIT_RANK[profile.credit_level] < CREDIT_RANK[p["min_credit"]]:
        reasons.append("征信等级不满足要求")
    if p.get("requires_collateral") and not profile.has_collateral:
        reasons.append("该产品需要抵押物")
    if p.get("need_tax_strict") and not profile.has_tax_record:
        reasons.append("需连续纳税记录")
    if p.get("need_tax_or_invoice") and not (profile.has_tax_record or profile.has_invoice):
        reasons.append("需纳税记录或稳定开票流水")
    if p.get("industry_fit") and profile.industry not in p["industry_fit"]:
        reasons.append("该产品面向特定行业")
    return (len(reasons) == 0, reasons)


def _estimate_amount(p: dict, profile: EnterpriseProfile, risk_mult: float = 1.0) -> float:
    """估算可贷额度(万元)。"""
    credit_amount = profile.annual_revenue * p["base_amount_ratio"]
    amount = credit_amount
    if p.get("requires_collateral") and profile.collateral_value > 0:
        amount = max(amount, profile.collateral_value * p.get("collateral_ratio", 0.7))
    # 征信加成
    credit_bonus = {"excellent": 1.15, "good": 1.0, "fair": 0.85, "poor": 0.7}
    amount *= credit_bonus.get(profile.credit_level, 1.0)
    # 风控评分整体调节
    amount *= risk_mult
    amount = min(amount, p["max_amount"])
    # 不超过用户期望金额太多,但允许给到期望值
    amount = min(amount, max(profile.loan_amount, amount))
    return round(amount, 1)


def _score(p: dict, profile: EnterpriseProfile, est_amount: float, rate: float) -> (int, List[str]):
    """对通过准入的产品综合打分。"""
    score = 50
    reasons = []

    # 额度满足度
    if est_amount >= profile.loan_amount:
        score += 20
        reasons.append(f"预估额度 {est_amount} 万元可满足你 {profile.loan_amount} 万元的需求")
    else:
        ratio = est_amount / profile.loan_amount if profile.loan_amount else 0
        score += int(20 * ratio)
        reasons.append(f"预估额度约 {est_amount} 万元,约为需求的 {int(ratio*100)}%")

    # 利率(越低越好)
    if rate <= 5:
        score += 20
        reasons.append(f"年化利率低至 {rate}%,资金成本优")
    elif rate <= 8:
        score += 12
        reasons.append(f"年化利率约 {rate}%,成本适中")
    elif rate <= 15:
        score += 4
    else:
        score -= 8
        reasons.append("利率偏高,建议仅作短期周转")

    # 征信加分
    cb = {"excellent": 12, "good": 8, "fair": 3, "poor": -5}
    score += cb.get(profile.credit_level, 0)

    # 急需放款匹配
    if profile.urgent and ("当天" in p["release_days"] or "1" in p["release_days"][:3]):
        score += 10
        reasons.append(f"放款快({p['release_days']}),契合你的急用需求")

    # 用途匹配
    if "purpose_fit" in p and profile.loan_purpose.value in p["purpose_fit"]:
        score += 8
        reasons.append("产品用途与你的贷款目的高度匹配")

    # 抵押带来的低息大额
    if p.get("requires_collateral") and profile.has_collateral:
        score += 6
        reasons.append("以抵押物撬动更大额度与更低利率")

    # 普惠政策优先
    if p["provider_type"] == "政策性/普惠":
        score += 6
        reasons.append("享受国家普惠金融政策支持")

    reasons.append(p["highlights"])
    return (max(0, min(100, score)), reasons)


def _approval_prob(score: int) -> str:
    if score >= 80:
        return "很高"
    if score >= 65:
        return "较高"
    if score >= 50:
        return "中等"
    return "偏低"


def _cautions(p: dict, profile: EnterpriseProfile, rate: float) -> List[str]:
    cautions = []
    if rate >= 15:
        cautions.append("利率较高,务必评估还款能力,避免长期使用")
    if p.get("requires_collateral"):
        cautions.append("需办理抵押登记,放款周期相对较长")
    if profile.has_overdue:
        cautions.append("当前存在逾期会影响审批与额度,建议先结清")
    term = min(profile.preferred_term_months, p["max_term_months"])
    if profile.preferred_term_months > p["max_term_months"]:
        cautions.append(f"该产品最长 {p['max_term_months']} 个月,短于你期望的 {profile.preferred_term_months} 个月")
    return cautions


def _improvement_tips(profile: EnterpriseProfile) -> List[str]:
    tips = []
    if profile.credit_level in ("fair", "poor"):
        tips.append("改善企业及法人征信(按时还款、降低负债率)可显著提升额度与利率")
    if profile.has_overdue:
        tips.append("优先结清当前逾期,征信修复后再申请更优产品")
    if not profile.has_tax_record:
        tips.append("建立规范连续的纳税记录,可解锁'银税互动'类低息信用贷")
    if not profile.has_invoice:
        tips.append("沉淀稳定的开票/经营流水,有助于提升信用额度评估")
    if not profile.has_collateral:
        tips.append("如有房产/设备等可抵押资产,可申请大额低息抵押经营贷")
    if profile.years_in_business < 2:
        tips.append("经营年限增长后(满 2 年),可申请门槛更高、利率更优的产品")
    return tips


def _personalized_advice(profile: EnterpriseProfile, risk: dict, plans) -> List[str]:
    """结合行业、规模、用途与风险画像生成定制化融资规划建议。"""
    advice: List[str] = []

    # 基于风险等级的整体策略
    grade = risk["grade"]
    if grade in ("A", "B"):
        advice.append(
            f"你的综合风控评分为 {risk['score']} 分(等级 {grade}·{risk['grade_label']}),"
            "资质较优,建议优先选择银行类低息产品,并可尝试争取更高授信额度与更长期限。")
    elif grade == "C":
        advice.append(
            f"综合风控评分 {risk['score']} 分(等级 {grade}·{risk['grade_label']}),"
            "建议适度控制单笔额度,优先选择审批友好的普惠或线上产品,稳健建立银行信用记录。")
    else:
        advice.append(
            f"综合风控评分 {risk['score']} 分(等级 {grade}·{risk['grade_label']}),"
            "当前直接获批优质产品难度较大,建议先小额周转、按时还款积累信用,再逐步申请低息产品。")

    # 负债杠杆
    dr = risk.get("debt_ratio")
    if dr is not None and dr > 0.6:
        suggest = round(profile.annual_revenue * 0.5, 1)
        advice.append(
            f"本次申请额度占年营收比例偏高,建议将单笔额度控制在 {suggest} 万元以内,"
            "或拆分为分期申请,降低还款压力与被拒风险。")

    # 用途匹配建议
    purpose_map = {
        "working_capital": "流动资金周转建议选择随借随还的信用类产品,按实际用款计息更灵活。",
        "equipment": "设备采购建议优先'设备分期/融资租赁',以设备为标的可降低首付、拉长期限。",
        "expansion": "扩大经营属中长期投入,建议搭配抵押经营贷等长期限产品,匹配回报周期。",
        "inventory": "备货采购具有季节性,建议用短期周转产品,旺季前申请、回款后结清。",
        "rd": "研发投入建议结合科技型企业政策性贷款与研发补助,降低综合成本。",
        "other": "建议明确资金用途,有助于银行评估并匹配更合适的产品。",
    }
    advice.append(purpose_map.get(profile.loan_purpose.value, ""))

    # 行业定制
    ind = profile.industry
    if ind == "餐饮":
        advice.append("餐饮行业现金流波动较大,建议预留 3 个月月供作为安全垫,优先选择可提前还款无违约金的产品。")
    elif ind == "制造业":
        advice.append("制造业可重点关注技改与设备更新类财政奖补,贷款+补贴组合能进一步摊薄资金成本。")
    elif ind == "科技":
        advice.append("科技企业建议完成科技型中小企业入库,叠加研发补助与知识产权质押融资拓宽渠道。")
    elif ind == "农业":
        advice.append("农业经营主体可叠加农业贴息与专项扶持,关注地方农业农村部门的季节性补贴窗口。")

    # 急用
    if profile.urgent and plans:
        fast = [p for p in plans if "当天" in p.expected_release_days or "1" in p.expected_release_days[:3]]
        if fast:
            advice.append(f"你标注了急需放款,【{fast[0].product_name}】放款最快({fast[0].expected_release_days}),可优先对接。")

    return [a for a in advice if a]


def _build_tiers(plans: List[RecommendedPlan], has_subsidy: bool) -> List[dict]:
    """从可申请方案中提炼三层差异化推荐:稳妥 / 冲刺 / 贴息最优。"""
    if not plans:
        return []
    tiers = []
    used = set()

    # 1) 稳妥方案:排除高息小贷,在本地通过率高的产品中选综合最优
    steady_pool = [p for p in plans
                   if p.provider_type != "小额贷款公司"
                   and (p.annual_rate_min + p.annual_rate_max) / 2 <= 12] or plans
    steady = max(steady_pool, key=lambda p: (p.local_approval_rate, p.score))
    tiers.append({
        "key": "steady", "name": "高通过率稳批版", "tagline": "审批最稳,优先求过",
        "product_id": steady.product_id, "product_name": steady.product_name,
        "headline": f"本地通过率 {steady.local_approval_rate}% · 通过率{steady.approval_probability}",
        "reason": f"该产品资质门槛友好、近三月本地审批通过率约 {steady.local_approval_rate}%,"
                  f"预估额度 {steady.estimated_amount} 万元,适合稳妥拿下放款。",
        "risk_note": steady.cautions[0] if steady.cautions else "整体风险较低",
    })
    used.add(steady.product_id)

    # 2) 冲刺方案:额度最高,标注门槛与风险
    sprint = max(plans, key=lambda p: (p.estimated_amount, p.score))
    tiers.append({
        "key": "sprint", "name": "额度拉满进阶版", "tagline": "额度拉满,博更高授信",
        "product_id": sprint.product_id, "product_name": sprint.product_name,
        "headline": f"最高额度 {sprint.estimated_amount} 万元 · 年化 {sprint.annual_rate_min}%-{sprint.annual_rate_max}%",
        "reason": f"该产品可冲刺最高 {sprint.estimated_amount} 万元额度,适合扩产/大额需求,"
                  f"但审批相对严格(本地通过率 {sprint.local_approval_rate}%)。",
        "risk_note": (sprint.hidden_criteria or "审批门槛较高,需备齐材料")
                     + ("。当前需抵押,放款偏慢" if sprint.requires_collateral else ""),
    })
    used.add(sprint.product_id)

    # 3) 贴息最优方案:综合年化最低,优先捆绑补贴
    def cost_key(p):
        mid = (p.annual_rate_min + p.annual_rate_max) / 2
        return (0 if p.subsidy_linked else 1, mid)
    subsidy = min(plans, key=cost_key)
    sub_extra = "可捆绑地方贴息政策,综合成本进一步下降" if (subsidy.subsidy_linked and has_subsidy) \
        else "综合年化最低,资金成本最优"
    after_subsidy = ""
    if subsidy.subsidy_linked and has_subsidy:
        rate_after = max(1.5, round((subsidy.annual_rate_min + subsidy.annual_rate_max) / 2 - 2.0, 2))
        save_year = round(subsidy.estimated_amount * 2.0 / 100, 2)
        save_month = round(save_year / 12, 2)
        after_subsidy = (f"叠加 2% 贴息后真实年化约 {rate_after}%,"
                         f"每年省息约 {save_year} 万、每月省约 {save_month} 万。")
    tiers.append({
        "key": "subsidy", "name": "财政补贴省钱版", "tagline": "成本最低,叠加补贴",
        "product_id": subsidy.product_id, "product_name": subsidy.product_name,
        "headline": f"综合年化 {subsidy.annual_rate_min}%-{subsidy.annual_rate_max}%"
                    + (" · 含贴息" if subsidy.subsidy_linked else ""),
        "reason": f"该产品年化利率最低({subsidy.annual_rate_min}%-{subsidy.annual_rate_max}%),{sub_extra}。",
        "risk_note": subsidy.cautions[0] if subsidy.cautions else "需满足政策申报条件",
        "after_subsidy": after_subsidy,
    })
    return tiers


def recommend(profile: EnterpriseProfile) -> RecommendResponse:
    risk = assess(profile)
    risk_mult = amount_multiplier(risk["score"])
    rate_adj = rate_adjustment(risk["score"])

    plans: List[RecommendedPlan] = []

    for p in PRODUCTS:
        ok, fail_reasons = _eligible(p, profile)
        if not ok:
            continue

        est_amount = _estimate_amount(p, profile, risk_mult)
        if est_amount <= 0:
            continue

        term = min(profile.preferred_term_months, p["max_term_months"])
        # 利率:征信越好越接近下限,再叠加风控评分调整
        rate_span = p["annual_rate_max"] - p["annual_rate_min"]
        credit_pos = {"excellent": 0.0, "good": 0.3, "fair": 0.6, "poor": 0.9}
        rate = p["annual_rate_min"] + rate_span * credit_pos.get(profile.credit_level, 0.5) + rate_adj
        rate = round(max(p["annual_rate_min"], min(p["annual_rate_max"], rate)), 2)

        score, match_reasons = _score(p, profile, est_amount, rate)
        monthly = _monthly_payment(est_amount, rate, term)
        total_interest = round(monthly * term - est_amount, 2)

        plans.append(RecommendedPlan(
            product_id=p["id"],
            product_name=p["name"],
            provider_type=p["provider_type"],
            score=score,
            approval_probability=_approval_prob(score),
            estimated_amount=est_amount,
            annual_rate_min=p["annual_rate_min"],
            annual_rate_max=p["annual_rate_max"],
            suggested_term_months=term,
            monthly_payment_estimate=monthly,
            total_interest_estimate=max(0.0, total_interest),
            requires_collateral=p.get("requires_collateral", False),
            expected_release_days=p["release_days"],
            match_reasons=match_reasons,
            cautions=_cautions(p, profile, rate),
            hidden_criteria=p.get("hidden_criteria", ""),
            local_approval_rate=p.get("local_approval_rate", 0),
            subsidy_linked=p.get("subsidy_linked", False),
        ))

    plans.sort(key=lambda x: x.score, reverse=True)

    highlights = [
        f"行业:{profile.industry} | 经营 {profile.years_in_business} 年 | 年营收 {profile.annual_revenue} 万元",
        f"征信:{ {'excellent':'优秀','good':'良好','fair':'一般','poor':'较差'}[profile.credit_level.value] }"
        + (" | 有抵押物" if profile.has_collateral else " | 无抵押物")
        + (" | 有纳税记录" if profile.has_tax_record else ""),
        f"需求:{profile.loan_amount} 万元 / {profile.preferred_term_months} 个月"
        + (" | 急需放款" if profile.urgent else ""),
    ]

    subsidies = match_policies(profile)
    advice = _personalized_advice(profile, risk, plans)
    tiers = [PlanTier(**t) for t in _build_tiers(plans, bool(subsidies))]

    best_amt = plans[0].estimated_amount if plans else 0.0
    guarantee = build_guarantee(profile, best_amt, profile.loan_amount)

    # 模型迭代:用历史真实通过率校准本行业方案的本地通过率
    cal = storage.calibrate_industry(profile.industry)
    if cal.get("calibrated") and plans:
        d = cal["delta"]
        for pl in plans:
            pl.local_approval_rate = max(40, min(99, pl.local_approval_rate + d))
        advice.insert(0, f"📊 已基于本行业 {cal['samples']} 笔真实申请数据校准:实际通过率 "
                         f"{cal['actual_pass_rate']}%,匹配越用越准。")

    if plans:
        best = plans[0]
        summary = (
            f"为你匹配到 {len(plans)} 个可申请方案,最优推荐【{best.product_name}】:"
            f"预估额度 {best.estimated_amount} 万元,年化 {best.annual_rate_min}%-{best.annual_rate_max}%,"
            f"通过率{best.approval_probability},{best.expected_release_days}放款。"
            f"综合风控评分 {risk['score']} 分(等级 {risk['grade']})。"
            + (f"另为你匹配到 {len(subsidies)} 项可申报的扶持政策。" if subsidies else "")
        )
    else:
        summary = (
            "根据当前资质暂未匹配到合适产品。通常是经营年限、营业额或征信未达门槛。"
            "请参考下方优化建议提升资质后再申请。"
            + (f"同时为你匹配到 {len(subsidies)} 项可申报的扶持政策。" if subsidies else "")
        )

    return RecommendResponse(
        summary=summary,
        profile_highlights=highlights,
        risk=RiskAssessment(**risk),
        improvement_tips=_improvement_tips(profile),
        personalized_advice=advice,
        subsidies=subsidies,
        plans=plans,
        tiers=tiers,
        guarantee=guarantee,
        plain_language=build_plain_language(
            plans=plans, risk=risk, subsidies=subsidies,
            requested_amount=profile.loan_amount, is_personal=False,
        ),
    )
