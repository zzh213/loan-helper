"""反欺诈与异常识别规则 + 分层产品匹配策略。

均为规则式(确定性),不依赖大模型,零成本稳定。用于:
1. 反欺诈拦截提示:虚假营业额、异常高估值、多头借贷等风险信号(仅提示,不硬拦)。
2. 分层匹配策略:根据资质画像给出主推产品方向,让用户看懂"为什么推这些"。
"""
from typing import Dict, List

from models import EnterpriseProfile


def detect_fraud_signals(profile: EnterpriseProfile) -> List[Dict]:
    """返回反欺诈/异常提示列表,每项:{code, level, title, detail, suggestion}。

    level:high(强烈异常,建议核实)/ mid(存疑,需佐证)/ info(温馨提示)。
    """
    alerts: List[Dict] = []
    rev = profile.annual_revenue or 0
    emp = profile.employees or 0
    cap = profile.registered_capital or 0
    amt = profile.loan_amount or 0
    col = profile.collateral_value or 0

    # 1. 虚假/夸大营业额:人均产出畸高,且无纳税、开票佐证
    if rev > 0 and emp > 0:
        per_head = rev / emp
        if per_head > 500 and not (profile.has_tax_record or profile.has_invoice):
            alerts.append({
                "code": "revenue_per_head",
                "level": "high",
                "title": "营业额与人员规模不匹配",
                "detail": f"人均年产出约 {int(per_head)} 万元/人,明显高于常见水平,且缺少纳税或开票佐证,银行进件时易被认定营收不实。",
                "suggestion": "以真实纳税申报表、对公流水或开票数据为准填写营业额,避免夸大导致直接拒件。",
            })

    # 2. 营业额远超注册资本且经营年限短(新企业虚高)
    if cap > 0 and rev > cap * 30 and profile.years_in_business < 2:
        alerts.append({
            "code": "revenue_vs_capital",
            "level": "mid",
            "title": "新企业营业额相对注册资本偏高",
            "detail": f"注册资本 {cap} 万、经营不足 2 年,却填报年营收 {rev} 万,数据合理性需佐证。",
            "suggestion": "准备真实经营流水与订单合同,说明高营收的业务来源。",
        })

    # 3. 抵押物估值异常偏高:远超营收且远超贷款需求
    if col > 0:
        if rev > 0 and col > rev * 10 and col > amt * 5:
            alerts.append({
                "code": "collateral_overvalue",
                "level": "high",
                "title": "抵押物估值异常偏高",
                "detail": f"填报抵押物估值 {col} 万,远超年营收与贷款需求,银行按市价 6-7 折重估后可能大幅缩水。",
                "suggestion": "以第三方评估或近期成交价填写抵押物估值,虚高估值不会提高实际额度。",
            })

    # 4. 多头借贷/过度授信信号:高杠杆 + 当前逾期
    if rev > 0:
        dr = amt / rev
        if dr > 1.0 and profile.has_overdue:
            alerts.append({
                "code": "multi_debt",
                "level": "high",
                "title": "疑似多头借贷 / 过度授信",
                "detail": f"贷款需求达年营收的 {int(dr*100)}% 且当前存在逾期,叠加多头借贷特征,风控大概率拦截。",
                "suggestion": "先结清逾期、下调额度至年营收 60% 以内,避免短期内向多家机构集中申请。",
            })
        elif dr > 1.5:
            alerts.append({
                "code": "over_leverage",
                "level": "mid",
                "title": "申请额度远超还款能力",
                "detail": f"贷款需求达年营收的 {int(dr*100)}%,远超常规授信上限,易被判定为过度融资。",
                "suggestion": "按经营真实资金缺口申请,分笔或分阶段融资更易获批。",
            })

    # 5. 差征信 + 急需放款:警惕高息陷阱与冲动借贷
    if profile.credit_level.value in ("fair", "poor") and profile.urgent and amt >= 50:
        alerts.append({
            "code": "urgent_poor_credit",
            "level": "info",
            "title": "征信偏弱 + 急需放款",
            "detail": "此类需求易被高综合成本产品吸引。请认准年化综合成本(IRR),警惕'秒批必过'类高息陷阱。",
            "suggestion": "优先选择持牌银行普惠产品,签约前务必核对全部费用口径。",
        })

    return alerts


def build_match_strategy(profile: EnterpriseProfile, risk: dict, plans) -> Dict:
    """根据资质画像给出分层匹配策略与主推产品方向。"""
    score = risk.get("score", 60)
    rev = profile.annual_revenue or 0
    amt = profile.loan_amount or 0
    term = profile.preferred_term_months or 12
    has_col = profile.has_collateral and (profile.collateral_value or 0) > 0
    plan_names = {pl.product_id: pl.product_name for pl in plans}

    if score < 55:
        segment = "低资质小微企业"
        seg_reason = f"综合风控 {score} 分(偏弱),以低门槛、看流水/纳税的信用类产品为主。"
        focus_ids = ["tax-credit-loan", "puhui-credit", "online-bank-flow", "pos-merchant-loan"]
        focus_label = "银税互动贷 / 普惠信用贷 / 流水贷"
        tips = [
            "优先补齐连续纳税记录,解锁银税互动贷(以纳税信用换额度)。",
            "无抵押可走政府性融资担保补足额度。",
        ]
    elif has_col and (profile.loan_purpose.value in ("equipment", "expansion") or amt > rev * 0.6):
        segment = "有设备/厂房可抵押"
        seg_reason = "具备抵押物,优先用抵押类产品放大额度、拉长期限、降低利率。"
        focus_ids = ["mortgage-biz-loan", "equipment-loan", "puhui-credit"]
        focus_label = "抵押经营贷 / 设备分期 / 厂房经营贷"
        tips = [
            "抵押物按市价 6-7 折评估,足额覆盖可显著提额降息。",
            "设备采购可用设备分期/融资租赁,以设备为标的、首付低。",
        ]
    elif amt >= max(200, rev * 0.8) and term >= 24:
        segment = "大额长期需求"
        seg_reason = "额度较大、期限较长,建议信用+抵押组合并叠加贴息,分散单一产品额度上限。"
        focus_ids = ["mortgage-biz-loan", "puhui-credit", "tax-credit-loan"]
        focus_label = "组合贷(信用 + 抵押 + 贴息)"
        tips = [
            "组合贷:信用额度打底 + 抵押额度补足,总额度更高、综合成本更优。",
            "叠加财政贴息产品,进一步降低实际年化成本。",
        ]
    else:
        segment = "资质良好常规需求"
        seg_reason = f"综合风控 {score} 分,资质均衡,可优先选低息普惠信用产品。"
        focus_ids = ["puhui-credit", "tax-credit-loan", "online-bank-flow"]
        focus_label = "普惠信用贷 / 银税互动贷"
        tips = ["资质较好,建议对比多家产品的年化综合成本后择优。"]

    focus = []
    for pid in focus_ids:
        if pid in plan_names:
            focus.append({"product_id": pid, "product_name": plan_names[pid], "matched": True})
        else:
            focus.append({"product_id": pid, "product_name": _DEFAULT_NAME.get(pid, pid), "matched": False})

    return {
        "segment": segment,
        "reason": seg_reason,
        "focus_label": focus_label,
        "focus_products": focus,
        "tips": tips,
    }


_DEFAULT_NAME = {
    "puhui-credit": "普惠小微信用贷",
    "tax-credit-loan": "银税互动信用贷",
    "online-bank-flow": "互联网银行流水贷",
    "mortgage-biz-loan": "抵押经营贷",
    "equipment-loan": "设备分期/融资租赁",
    "pos-merchant-loan": "商户收单流水贷",
}
