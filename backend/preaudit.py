"""前置预审模块:提交申请前,模拟风控打分并输出可优化的整改建议。

核心痛点:小微企业最怕提交资料后被拒贷,在征信留下硬查询污点。
本模块在提交前先做一次"预审",把扣分短板和可优化方案逐条列出,
让用户先补短板、再正式申请,提升通过率、避免无谓的征信查询。
"""
from typing import List, Optional

import risk
from models import EnterpriseProfile

CREDIT_BASE = risk.CREDIT_BASE


def _debt_ratio(p: EnterpriseProfile) -> Optional[float]:
    if p.annual_revenue <= 0:
        return None
    return round(p.loan_amount / p.annual_revenue, 2)


def build_preaudit(profile: EnterpriseProfile) -> dict:
    """返回前置预审报告:总分、结论、扣分短板及整改方案、可恢复分。"""
    base = risk.assess(profile)
    score = base["score"]
    weaknesses: List[dict] = []
    recoverable = 0

    # 1. 当前逾期(最高风险项)
    if profile.has_overdue:
        recoverable += 18
        weaknesses.append({
            "title": "存在当前逾期", "minus": 18, "severity": "high",
            "issue": "征信报告显示当前有逾期,绝大多数银行会直接拒贷。",
            "fix": "优先结清逾期欠款,结清后保持 1-3 个月良好记录再申请;可先开具结清证明。",
        })

    # 2. 征信等级偏低
    if profile.credit_level.value == "poor":
        recoverable += 12
        weaknesses.append({
            "title": "征信等级较差", "minus": 12, "severity": "high",
            "issue": "历史逾期较多,信用分被压低,额度低、利率高。",
            "fix": "近半年保持按时还款,降低信用卡使用率至 70% 以下;优先选择银税贷/抵押类增信产品。",
        })
    elif profile.credit_level.value == "fair":
        recoverable += 6
        weaknesses.append({
            "title": "征信轻微逾期", "minus": 6, "severity": "medium",
            "issue": "有少量历史逾期记录,部分银行审批趋严。",
            "fix": "保持后续 0 逾期,3 个月后征信表现可上修;申请时附情况说明可减弱影响。",
        })

    # 3. 经营年限短
    if profile.years_in_business < 1:
        recoverable += 8
        weaknesses.append({
            "title": "经营年限不足 1 年", "minus": 8, "severity": "high",
            "issue": "初创企业被视为高风险,可选产品少。", "severity_label": "高",
            "fix": "补充法人其他经营实体流水/个人征信增信;选择对年限要求低的担保/抵押产品。",
        })
    elif profile.years_in_business < 3:
        weaknesses.append({
            "title": "经营年限偏短", "minus": 0, "severity": "low",
            "issue": "经营 1-3 年,处于成长期,大额信用贷受限。",
            "fix": "积累连续开票与纳税记录,满 3 年后额度系数显著提升。",
        })

    # 4. 抵押物不足
    if not (profile.has_collateral and profile.collateral_value > 0):
        recoverable += 7
        weaknesses.append({
            "title": "缺少抵押物", "minus": 7, "severity": "medium",
            "issue": "无抵押增信,纯信用贷额度有限。",
            "fix": "补充门店租赁合同、设备清单或房产证明;可引入担保人或选银税信用贷。",
        })

    # 5. 纳税/开票缺失
    if not profile.has_tax_record and not profile.has_invoice:
        recoverable += 10
        weaknesses.append({
            "title": "缺少纳税与开票凭证", "minus": 4, "severity": "medium",
            "issue": "经营真实性难以验证,银税类低息产品无法解锁。",
            "fix": "补充近 6-12 个月对公流水、连续纳税申报及开票记录,可激活低息银税贷。",
        })
    elif not profile.has_tax_record:
        weaknesses.append({
            "title": "无连续纳税记录", "minus": 6, "severity": "low",
            "issue": "无法匹配纯银税信用产品。",
            "fix": "保持连续申报,半年后即可申请纳税贷类低息产品。",
        })

    # 6. 杠杆偏高
    dr = _debt_ratio(profile)
    if dr is not None and dr > 0.6:
        recoverable += 10
        weaknesses.append({
            "title": "贷款需求杠杆偏高", "minus": 10, "severity": "medium",
            "issue": f"申请额约为年营收的 {int(dr*100)}%,超出常规授信比例,易被压额或拒批。",
            "fix": "建议下调首次申请额度至年营收 50% 以内,或分两期申请、提供更多流水佐证。",
        })

    target = min(95, score + recoverable)
    if score >= 70:
        verdict, verdict_label = "pass", "资质良好,可直接提交申请"
    elif score >= 55:
        verdict, verdict_label = "optimize", "建议先补短板再提交,可显著提高通过率"
    else:
        verdict, verdict_label = "risk", "当前直接申请易被拒,务必先整改后再提交"

    return {
        "score": score,
        "grade": base["grade"],
        "grade_label": base["grade_label"],
        "verdict": verdict,
        "verdict_label": verdict_label,
        "recoverable": recoverable,
        "target_score": target,
        "weaknesses": weaknesses,
        "factors": base["factors"],
    }
