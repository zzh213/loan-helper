"""客户经理标准化跟进 SOP 生成。

根据线索(行业、金额、需求标签、状态)生成:初次沟通话术、材料清单、跟进节奏提醒。
让客户经理接手即有标准动作,提高转化与专业度。
"""
from typing import Dict, List

# 各状态对应的下一步跟进动作与提醒节奏
_STAGE_ACTIONS = {
    "待回访": ("首次电联", "24 小时内首次联系,超时流失率显著上升", "尽快首次电联,确认需求真实性与紧急度"),
    "已联系": ("需求确认 + 收资料", "2 个工作日内引导补齐材料", "发送材料清单,约定收资料时间"),
    "材料待补充": ("催办材料", "每 2 天跟进一次,避免客户流失", "逐项核对缺失材料,协助企业准备"),
    "银行审核中": ("进度跟踪", "每 3 天与银行/客户各同步一次进度", "跟踪银行审批进度,及时反馈客户"),
    "已放款": ("成单回访 + 转介绍", "放款后 7 天回访,引导老客裂变", "确认放款到账,邀请推荐同行得权益"),
    "已拒绝": ("拒因分析 + 备选方案", "拒贷后 1 周内提供替代路径", "分析拒贷原因,匹配增信/备选产品"),
}

_INDUSTRY_MATERIALS = {
    "制造": ["营业执照", "近 12 个月对公流水", "近 1 年纳税申报表", "设备/厂房权属证明", "主要购销合同"],
    "商贸": ["营业执照", "近 12 个月对公+法人流水", "进销存/开票数据", "上下游合作协议", "库存与应收清单"],
    "餐饮": ["营业执照", "近 6 个月经营流水(含收款码)", "门店租赁合同", "食品经营许可证", "外卖平台流水"],
    "建筑": ["营业执照", "对公流水", "在手工程合同", "资质证书", "工程回款/进度证明"],
    "科技": ["营业执照", "对公流水", "纳税记录", "知识产权/软著证书", "订单或研发合同"],
    "物流": ["营业执照", "对公流水", "车辆行驶证/运输资质", "运输合同", "油卡/ETC 消费凭证"],
}
_DEFAULT_MATERIALS = ["营业执照", "近 12 个月对公流水", "近 1 年纳税申报表", "法人身份证", "经营场所证明"]


def _opening_script(lead: Dict) -> str:
    company = lead.get("company_name") or "您好"
    amt = lead.get("loan_amount") or 0
    ind = lead.get("industry") or ""
    amt_txt = f"约 {amt} 万元" if amt else "的融资"
    return (
        f"您好,请问是{company}的负责人吗?我是小微贷管家的专属融资顾问。"
        f"看到您在平台完成了{ind}行业{amt_txt}的测算,系统已为您匹配到合适的银行方案。"
        f"想跟您确认下资金用途和到账时间要求,帮您锁定通过率最高、成本最低的产品,方便现在沟通两分钟吗?"
    )


def build_sop(lead: Dict) -> Dict:
    status = lead.get("status") or "待回访"
    action, cadence, tip = _STAGE_ACTIONS.get(status, _STAGE_ACTIONS["待回访"])
    ind = lead.get("industry") or ""
    materials = _INDUSTRY_MATERIALS.get(ind, _DEFAULT_MATERIALS)

    tags = lead.get("tags") or ""
    focus: List[str] = []
    if "大额抵押" in tags:
        focus.append("大额需求:优先核实抵押物权属与估值,主推抵押/组合贷")
    if "短期周转" in tags:
        focus.append("短期周转:主推银税贷/信用贷,强调放款速度")
    if "贴息" in tags:
        focus.append("有贴息意向:同步匹配可申报补贴,可引导政策代办增值服务")

    amt = lead.get("loan_amount") or 0
    if amt >= 150:
        recommend = "抵押经营贷 / 组合贷(信用+抵押叠加贴息)"
    elif amt and amt < 50:
        recommend = "普惠信用贷 / 银税贷(免抵押、放款快)"
    else:
        recommend = "银税贷 / 设备抵押贷(按增信情况择优)"

    return {
        "next_action": action,
        "cadence": cadence,
        "tip": tip,
        "opening_script": _opening_script(lead),
        "materials": materials,
        "focus": focus,
        "recommend_product": recommend,
    }
