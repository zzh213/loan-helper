"""大白话解读:把专业的贷款方案翻译成小企业主/普通人都能看懂的日常语言。

纯规则生成,不依赖大模型,稳定且零成本。企业贷款与个人贷款共用。
"""
from typing import List, Optional


# 常见术语的大白话解释(名词小课堂)
GLOSSARY = [
    {"term": "年化利率", "plain": "借一年要付多少利息的比例。比如年化 6%,借 1 万块用一年,利息大概 600 块。"},
    {"term": "预估额度", "plain": "银行大概愿意借给您的最高金额。这是上限,您用多少借多少,不用全借。"},
    {"term": "月供", "plain": "每个月要还的钱,包含借的本金和利息。心里按这个数衡量还得起就没问题。"},
    {"term": "抵押", "plain": "拿房子、车、设备这些值钱的东西作担保。还不上时银行可以处置它。写着『免抵押』就是不用押东西。"},
    {"term": "征信", "plain": "您(或企业)过去借钱还钱的信用记录。一直按时还,征信就好,越容易借到钱、利息也更低。"},
    {"term": "通过率", "plain": "大概有多大机会能批下来。数字越高越稳,但最终还要看实际提交的材料。"},
    {"term": "放款时效", "plain": "从提交申请到钱真正到账,大概要等多久。急用钱就重点看这一项。"},
    {"term": "担保增信", "plain": "找一家担保公司帮您做担保,让银行更放心。抵押物不够时,靠它能多借一些。"},
    {"term": "贴息 / 补贴", "plain": "政府帮您承担一部分利息,或直接给一笔钱,实实在在减轻还款负担,记得申请。"},
    {"term": "风控评分", "plain": "系统综合您的经营、收入、信用等情况打的分。分越高,越容易借到钱、条件也越好。"},
]

_GRADE_PLAIN = {
    "A": "在放款机构眼里您属于优质客户,基本不用太担心批不批,条件也谈得好。",
    "B": "您的资质挺不错,大多数机构都愿意放款,把材料备齐就比较稳。",
    "C": "属于中等水平,能借,但材料准备得越齐、越真实,批下来越有把握。",
    "D": "目前资质稍微吃力一点,建议先照下面的建议改善几项,再申请会顺很多。",
}


def _amount_sentence(est_amount: float, requested: float) -> str:
    if requested <= 0:
        return f"这个方案大概能给您批 {est_amount} 万元。"
    if est_amount >= requested:
        return (f"您想借 {requested} 万元,这个方案大概能批到 {est_amount} 万元,"
                f"够用了。")
    gap = round(requested - est_amount, 1)
    return (f"您想借 {requested} 万元,这个方案大概能批 {est_amount} 万元,"
            f"比想要的少 {gap} 万元。差的这部分,可以看下面的『担保增信』方案来补上。")


def build_plain_language(
    *,
    plans: List,
    risk: dict,
    subsidies: List,
    requested_amount: float = 0.0,
    is_personal: bool = False,
) -> dict:
    """根据推荐结果生成大白话解读。plans / subsidies 可为空。"""
    who = "您" if is_personal else "您企业"
    paragraphs: List[str] = []
    next_steps: List[str] = []

    if plans:
        best = plans[0]
        # 1) 能借多少
        paragraphs.append("先说最要紧的:" + _amount_sentence(best.estimated_amount, requested_amount))

        # 2) 利息成本,用具体金额讲
        cost = (f"利息方面,这个方案年化利率大约 {best.annual_rate_min}%-{best.annual_rate_max}%。"
                f"通俗讲,就是借 100 块钱、用满一年,大概花 {best.annual_rate_min}-{best.annual_rate_max} 块钱利息。")
        if best.monthly_payment_estimate and best.suggested_term_months:
            cost += (f"按这个方案算,分 {best.suggested_term_months} 个月还,"
                     f"每个月大概还 {best.monthly_payment_estimate} 万元;")
            if best.total_interest_estimate:
                cost += f"整个过程总共大概付 {best.total_interest_estimate} 万元利息。"
        paragraphs.append(cost)

        # 3) 要不要抵押 + 多久放款
        collat = ("这个方案需要用房产、车辆等值钱的东西作抵押;"
                  if best.requires_collateral
                  else "这个方案不用抵押任何东西,手续相对省事;")
        collat += f"从申请到钱到账,大概 {best.expected_release_days}。"
        paragraphs.append(collat)

        # 4) 风控等级白话
        grade = risk.get("grade", "C")
        paragraphs.append(
            f"系统给{who}打了 {risk.get('score', 0)} 分(等级 {grade})。"
            + _GRADE_PLAIN.get(grade, "")
            + f"这个方案预估通过率 {best.approval_probability}。"
        )

        next_steps.append("点上方『材料清单』,照着把要交的材料准备齐。")
        next_steps.append("材料备好后,带着去对应的银行或机构申请就行。")
    else:
        paragraphs.append(
            f"根据{who}目前的情况,暂时还没匹配到合适的贷款产品。别灰心,"
            "这通常是经营年限、营业额或征信还差一点点没到门槛,是可以慢慢补上的。"
        )
        paragraphs.append(
            "下面的『提升资质』里列了几条具体建议,照着做一段时间,资质上来了再申请,"
            "多半就能批下来。"
        )
        next_steps.append("看下面『提升资质·获得更优方案』,挑一两条先做起来。")

    # 补贴提醒(两种情况都提)
    if subsidies:
        paragraphs.append(
            f"另外一个好消息:{who}可能还能申请 {len(subsidies)} 项政府扶持政策(见下方"
            "『扶持政策』)。相当于国家帮您分担一部分利息或给一笔补贴,是白拿的实惠,千万别漏了。"
        )
        next_steps.append("翻到下方『扶持政策』,看看哪几项能申请,按申请要点去办。")

    return {
        "title": "💬 说人话版解读",
        "intro": "怕专业名词看不懂?这里用大白话给您把上面的方案讲清楚:",
        "paragraphs": paragraphs,
        "next_steps": next_steps,
        "glossary": GLOSSARY,
    }
