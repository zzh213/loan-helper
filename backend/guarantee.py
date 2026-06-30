"""政府性融资担保增信方案。

抵押物不足、信用额度不够时,引入本地政府性融资担保公司增信,补满额度缺口。
担保费由财政贴费,综合成本低,是通用AI难以整合的线下资源。
"""
from typing import Optional

from models import EnterpriseProfile

# 政府性担保贴费后年费率约 0.5%-1%,这里取常见 0.8%
GUARANTEE_FEE_RATE = 0.8
MAX_RATIO = 0.8  # 担保增信可补的额度上限 = 营收 * 该比例


def build_guarantee(profile: EnterpriseProfile, best_amount: float, demand: float) -> Optional[dict]:
    """无抵押且额度有缺口时,生成担保增信方案。"""
    gap = round(demand - best_amount, 1)
    if profile.has_collateral or gap <= 0:
        return None
    cap = round(profile.annual_revenue * MAX_RATIO, 1)
    boosted = round(min(demand, best_amount + min(gap, cap)), 1)
    fee = round(boosted * GUARANTEE_FEE_RATE / 100, 2)
    return {
        "title": "政府性融资担保增信方案",
        "tagline": "无抵押也能补满额度",
        "base_amount": best_amount,
        "boosted_amount": boosted,
        "fill_gap": round(boosted - best_amount, 1),
        "fee_rate": GUARANTEE_FEE_RATE,
        "annual_fee": fee,
        "reason": f"你暂无抵押物,缺口约 {gap} 万元。引入政府性融资担保公司增信后,"
                  f"额度可提升至约 {boosted} 万元,担保年费率仅 {GUARANTEE_FEE_RATE}%(财政贴费),约 {fee} 万元/年。",
        "steps": ["提交担保申请与经营材料", "担保公司线下尽调", "出具担保函", "银行凭担保函放款"],
        "note": "政府性担保聚焦小微首贷/信用贷,反担保要求低;具体额度以担保公司尽调为准。",
    }
