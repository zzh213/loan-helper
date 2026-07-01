"""个人扶持政策 / 贴息 / 补贴匹配。

返回与企业端一致的 SubsidyPolicy 结构,便于前端复用同一渲染。
数据为 2024–2025 全国普遍性政策口径,具体额度与条件以当地人社、
财政、住建、税务等部门最新文件为准。
"""
from typing import List

from models import PersonalProfile, SubsidyPolicy


def match_personal_policies(p: PersonalProfile) -> List[SubsidyPolicy]:
    items: List[SubsidyPolicy] = []

    # 创业担保贷款贴息(创业 / 个体)
    if p.is_entrepreneur or p.loan_purpose.value == "startup":
        items.append(SubsidyPolicy(
            id="startup-guarantee-subsidy",
            name="创业担保贷款贴息",
            category="创业扶持",
            authority="人社局 / 财政局",
            benefit="个人最高 30 万元(合伙可叠加),贷款期限内由财政按 LPR 给予贴息,实际利息成本极低",
            apply_points="持营业执照 + 属于扶持人群(高校毕业生/返乡农民工/退役军人/登记失业等),向创业地人社部门或经办银行申请",
            apply_window="常年可申报,名额有限先到先得",
        ))

    # 公积金相关
    if p.has_housing_fund:
        items.append(SubsidyPolicy(
            id="housing-fund-benefit",
            name="住房公积金贷款 / 提取",
            category="住房支持",
            authority="住房公积金管理中心",
            benefit="购房可用公积金贷款,利率远低于商业贷款;租房、装修、大病等情形可按规定提取账户余额",
            apply_points="连续缴存满 6-12 个月;通过当地公积金 App / 中心线上办理",
            apply_window="常年可申报",
        ))

    # 高校毕业生
    if "高校毕业生" in p.special_identity or (p.age <= 26 and p.occupation_type.value in ("freelancer", "student", "self_employed")):
        items.append(SubsidyPolicy(
            id="graduate-support",
            name="高校毕业生创业就业扶持",
            category="人才补贴",
            authority="人社局 / 团委",
            benefit="一次性创业补贴、创业场租补贴、灵活就业社保补贴,部分城市叠加租房与生活补贴",
            apply_points="毕业 5 年内、办理就业创业登记;凭毕业证与营业执照/劳动合同申报",
            apply_window="毕业 5 年内",
        ))

    # 退役军人
    if "退役军人" in p.special_identity:
        items.append(SubsidyPolicy(
            id="veteran-support",
            name="退役军人创业就业专项扶持",
            category="创业扶持",
            authority="退役军人事务局 / 人社局",
            benefit="创业担保贷款个人最高 50 万元(高于普通个人的 30 万)、税费减免、免费创业培训与场地扶持",
            apply_points="凭退役证向退役军人事务部门申报",
            apply_window="常年可申报",
        ))

    # 灵活就业社保补贴
    if p.occupation_type.value == "freelancer" or (not p.has_social_security and p.occupation_type.value in ("self_employed", "freelancer")):
        items.append(SubsidyPolicy(
            id="flexible-employment-subsidy",
            name="灵活就业人员社保补贴",
            category="社保补贴",
            authority="人社局",
            benefit="就业困难人员/离校未就业毕业生以灵活就业身份缴纳社保,可申请社保补贴(多为缴费额的 2/3),一般不超过 3 年,'4050'人员可延长至 5 年",
            apply_points="办理灵活就业登记并按时缴纳社保后,向社区/人社部门申报",
            apply_window="按年申报,补贴期限一般不超过 3 年('4050'人员可延至 5 年)",
        ))

    # 返乡农民工
    if "返乡农民工" in p.special_identity:
        items.append(SubsidyPolicy(
            id="returning-worker-support",
            name="返乡入乡创业扶持",
            category="创业扶持",
            authority="人社局 / 农业农村局",
            benefit="创业担保贷款贴息、一次性创业补贴、创业园区租金减免",
            apply_points="返乡创业并办理营业执照,向户籍地或创业地人社部门申报",
            apply_window="常年可申报",
        ))

    # 大病 / 医疗
    if p.loan_purpose.value == "medical":
        items.append(SubsidyPolicy(
            id="medical-assistance",
            name="医保报销与大病救助",
            category="医疗保障",
            authority="医保局 / 民政局",
            benefit="先走基本医保 + 大病保险报销,困难家庭可申请医疗救助,能显著降低自付,减少举债金额",
            apply_points="在借款前先办理医保报销与救助申请,按实际自付缺口再申请贷款",
            apply_window="常年可申报",
        ))

    return items
