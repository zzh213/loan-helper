"""补贴与扶持政策库及匹配逻辑。

政策为面向中小微企业的常见普惠/财税/就业/科技类扶持的示意性整理,
具体以当地主管部门最新公告为准。可按地区扩展。
"""
from typing import Callable, Dict, List

from models import EnterpriseProfile

# 每条政策包含:匹配条件函数 cond、说明、申请要点、主管部门、类别
POLICIES: List[Dict] = [
    {
        "id": "puhui-interest-subsidy", "apply_window": "常年滚动,放款后90天内申报",
        "name": "普惠小微贷款贴息",
        "category": "财政贴息",
        "authority": "地方财政局 / 工信局",
        "benefit": "对符合条件的小微企业贷款给予 1%-2% 的利息补贴,降低融资成本",
        "apply_points": "持有效营业执照、贷款合同与放款凭证,向当地政务服务中心或银行联合申报",
        "cond": lambda p: p.annual_revenue <= 2000 and p.years_in_business >= 0.5,
    },
    {
        "id": "tech-sme-grant", "apply_window": "每年3-5月集中入库评价",
        "name": "科技型中小企业研发补助",
        "category": "科技创新",
        "authority": "科技局 / 科委",
        "benefit": "通过科技型中小企业评价入库后,研发费用可享受加计扣除及专项研发补助",
        "apply_points": "在'科技型中小企业信息库'完成入库评价,留存研发项目立项与费用台账",
        "cond": lambda p: p.industry == "科技" or p.loan_purpose.value == "rd",
    },
    {
        "id": "startup-guarantee-loan", "apply_window": "常年可申报",
        "name": "创业担保贷款及贴息",
        "category": "创业就业",
        "authority": "人社局 / 担保中心",
        "benefit": "符合条件的初创企业可申请创业担保贷款,财政全额或部分贴息",
        "apply_points": "提供营业执照、带动就业证明(吸纳一定数量就业人员),经担保机构审核",
        "cond": lambda p: p.years_in_business <= 3 and p.employees >= 1,
    },
    {
        "id": "stabilize-employment", "apply_window": "每年Q1集中受理",
        "name": "稳岗扩岗补贴",
        "category": "创业就业",
        "authority": "人社局",
        "benefit": "按企业参保职工人数给予稳岗返还或一次性扩岗补助",
        "apply_points": "依法为员工缴纳社保、无大规模裁员,通过人社部门线上系统申报",
        "cond": lambda p: p.employees >= 5,
    },
    {
        "id": "manufacturing-upgrade", "apply_window": "项目验收后,每季度末申报",
        "name": "制造业技改 / 设备更新补贴",
        "category": "产业升级",
        "authority": "工信局 / 发改委",
        "benefit": "对技术改造、设备更新投资按比例给予事后奖补",
        "apply_points": "提交技改项目方案、设备采购合同与发票,完成项目验收后申报奖补",
        "cond": lambda p: p.industry == "制造业" and p.loan_purpose.value in ("equipment", "expansion"),
    },
    {
        "id": "agri-support", "apply_window": "春耕/秋收两季窗口",
        "name": "农业经营主体扶持补贴",
        "category": "乡村振兴",
        "authority": "农业农村局",
        "benefit": "面向农业经营主体的生产、设施与贷款贴息扶持",
        "apply_points": "提供农业经营资质与项目材料,向当地农业农村部门申报",
        "cond": lambda p: p.industry == "农业",
    },
    {
        "id": "tax-relief-small", "apply_window": "汇算清缴期(次年5月底前)",
        "name": "小微企业税费减免",
        "category": "财税优惠",
        "authority": "税务局",
        "benefit": "符合小型微利企业标准可享受企业所得税优惠及增值税起征点优惠",
        "apply_points": "按规范进行纳税申报,在汇算清缴时享受小型微利企业政策",
        "cond": lambda p: p.annual_revenue <= 3000,
    },
    {
        "id": "rent-subsidy", "apply_window": "入驻后6个月内,常年受理",
        "name": "创业孵化 / 房租补贴",
        "category": "创业就业",
        "authority": "人社局 / 园区管委会",
        "benefit": "入驻创业孵化基地或园区的小微企业可申请房租减免或补贴",
        "apply_points": "入驻认定的孵化载体,提供租赁合同,向园区或人社部门申报",
        "cond": lambda p: p.years_in_business <= 5 and p.annual_revenue <= 1000,
    },
]


def match_policies(profile: EnterpriseProfile) -> List[Dict]:
    """返回匹配到的补贴政策列表。"""
    matched = []
    for pol in POLICIES:
        try:
            if pol["cond"](profile):
                matched.append({
                    "id": pol["id"],
                    "name": pol["name"],
                    "category": pol["category"],
                    "authority": pol["authority"],
                    "benefit": pol["benefit"],
                    "apply_points": pol["apply_points"],
                    "apply_window": pol.get("apply_window", "常年可申报"),
                    "updated": pol.get("updated", "2026-06"),
                })
        except Exception:
            continue
    return matched
