"""政策申报指南生成:根据政策信息生成结构化的纯文本申报指引。"""
from typing import Dict


def build_policy_guide(pol: Dict) -> str:
    """生成一份可下载的政策申报指南(纯文本)。"""
    name = pol.get("name", "")
    lines = []
    lines.append("=" * 40)
    lines.append(f"  {name} · 申报指南")
    lines.append("=" * 40)
    lines.append("")
    lines.append(f"【政策类别】{pol.get('category', '-')}")
    lines.append(f"【主管部门】{pol.get('authority', '-')}")
    lines.append(f"【适用行业】{'、'.join(pol.get('industries', ['通用']))}")
    lines.append(f"【适用规模】{'、'.join(pol.get('scale', ['小微']))}")
    lines.append(f"【申报窗口】{pol.get('apply_window', '常年可申报')}")
    lines.append(f"【更新时间】{pol.get('updated', '-')}")
    lines.append("")
    lines.append("一、政策内容")
    lines.append(f"  {pol.get('benefit', '')}")
    lines.append("")
    lines.append("二、申报要点")
    lines.append(f"  {pol.get('apply_points', '')}")
    lines.append("")
    lines.append("三、通用申报流程")
    for i, step in enumerate([
        "确认企业是否满足政策适用条件(行业、规模、窗口期)",
        "准备基础材料:营业执照、近期纳税/财务凭证、开户许可或银行流水",
        "登录当地政务服务网 / 主管部门官网,查询该政策的最新申报通知",
        "按通知要求填写申报表并上传证明材料,线上或窗口提交",
        "跟踪受理与审核进度,按要求补充材料",
        "审批通过后,按拨付方式领取贴息 / 补贴 / 减免",
    ], 1):
        lines.append(f"  {i}. {step}")
    lines.append("")
    lines.append("四、常见所需材料清单")
    for m in [
        "营业执照副本复印件(加盖公章)",
        "法定代表人身份证复印件",
        "近一年纳税申报表 / 完税证明",
        "近期财务报表或银行对账单",
        "与政策相关的专项材料(如项目立项书、租赁合同、参保证明等)",
    ]:
        lines.append(f"  · {m}")
    lines.append("")
    lines.append("-" * 40)
    lines.append("温馨提示:本指南为通用参考,具体额度、条件与申报窗口")
    lines.append("以当地主管部门最新公示为准。本平台仅提供信息匹配服务,")
    lines.append("不代办申报、不收取前置费用。")
    lines.append("-" * 40)
    return "\n".join(lines)
