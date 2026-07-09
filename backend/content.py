"""资讯专栏内容库:小微企业融资科普、贴息政策更新、避坑指南。

用于冷启动内容获客(抖音/百度/知乎图文素材同源),前台可读、后台可维护。
自定义文章持久化在 settings 表,与内置文章合并展示。
"""
import json
import uuid
from typing import Dict, List, Optional

import storage

# 内容分类
CATEGORIES = ["融资科普", "贴息政策", "避坑指南", "行业干货"]

# 内置文章库(平台原创科普,合规、不含绝对化宣传)
ARTICLES: List[Dict] = [
    {
        "id": "guide-yinshui",
        "category": "融资科普",
        "title": "银税贷是什么?纳税良好的小微企业如何用它免抵押融资",
        "summary": "把纳税信用变成授信额度。讲清银税贷的准入门槛、额度测算逻辑与申请材料。",
        "tags": ["银税贷", "纳税信用", "免抵押"],
        "read_min": 4,
        "updated": "2026-07-01",
        "body": [
            ("什么是银税贷", "银税贷是银行依据企业连续、真实的纳税记录发放的信用贷款,无需抵押物。核心逻辑是:按时足额纳税=经营真实且有还款能力,银行以此作为授信依据。"),
            ("哪些企业适合", "成立满 1-2 年、纳税信用等级 B 级及以上、近 12 个月有连续纳税记录的小微企业最匹配。餐饮、商贸、制造等有稳定开票的行业尤其适用。"),
            ("额度怎么测算", "常见口径是按年纳税额的一定倍数授信(不同银行差异较大),或参考年开票额的一定比例。具体额度以银行审批为准,可在本平台先做智能测算获得参考区间。"),
            ("申请材料清单", "营业执照、近 12 个月对公流水、近 1 年纳税申报表、法人身份证、经营场所证明。纳税信用等级可在电子税务局查询。"),
            ("提示", "本平台仅提供信息匹配与测算参考,不放贷,最终授信与利率以持牌银行审批结果为准。请认准年化综合成本(IRR)口径,警惕任何要求前置收费的行为。"),
        ],
    },
    {
        "id": "guide-equipment",
        "category": "行业干货",
        "title": "制造业设备抵押贷全攻略:用机器设备撬动经营资金",
        "summary": "有设备、有厂房的制造企业如何用固定资产做抵押,获得更高额度与更低利率。",
        "tags": ["设备抵押", "制造业", "厂房经营贷"],
        "read_min": 5,
        "updated": "2026-06-28",
        "body": [
            ("设备抵押贷的优势", "相比纯信用贷,以设备/厂房抵押通常能获得更高额度、更长期限和更低利率,适合有大额、长期资金需求的制造企业。"),
            ("哪些资产可抵押", "自有产权的生产设备、厂房、土地使用权等。设备需权属清晰、可评估、有一定残值;融资租赁或已抵押的设备一般不可再抵押。"),
            ("估值与成数", "银行会对抵押物做评估,按评估值的一定成数放款(设备通常成数低于房产)。设备越通用、越易变现,成数越高。"),
            ("组合方案更划算", "大额需求可采用组合贷:信用额度 + 抵押额度叠加,再匹配贴息政策,综合成本更低。可在本平台测算组合贷方案。"),
            ("提示", "抵押物估值以评估机构与银行认定为准。平台提供方案匹配与材料整理参考,不收取前置费用。"),
        ],
    },
    {
        "id": "policy-tiexi-2026",
        "category": "贴息政策",
        "title": "2026 年小微企业贴息补贴怎么申报?一文看懂流程与材料",
        "summary": "贴息不是自动到账,需主动申报。梳理常见贴息类型、申报窗口与材料准备。",
        "tags": ["贴息", "补贴申报", "普惠金融"],
        "read_min": 4,
        "updated": "2026-07-05",
        "body": [
            ("贴息补贴的常见类型", "包括创业担保贷款贴息、科技型企业贷款贴息、稳岗扩岗补贴、产业升级技改贴息等。不同地区、园区政策差异较大。"),
            ("申报的关键前提", "多数贴息要求'先贷款、后申报',需先在合作银行成功放款,再凭放款凭证向主管部门申报。部分政策有行业、规模、注册地限制。"),
            ("申报流程", "① 确认符合政策条件 → ② 准备材料(营业执照、贷款合同、放款凭证、纳税证明等) → ③ 在规定窗口内提交主管部门 → ④ 审核公示 → ⑤ 贴息资金拨付。"),
            ("常见误区", "错过申报窗口、材料不全、不了解本地/园区级隐藏政策是三大常见丢分点。建议用本平台'隐藏贴息专区'按注册地精准匹配。"),
            ("提示", "以上为通用指引,具体政策、窗口、材料以主管部门最新公告为准。平台可提供政策匹配与申报清单,政策代办为可选付费服务,不成功不收费。"),
        ],
    },
    {
        "id": "avoid-scam",
        "category": "避坑指南",
        "title": "小微融资六大常见套路:遇到这些情况请立即止损",
        "summary": "识别'包装征信''前置收费''AB 贷'等高风险陷阱,守住你的钱和征信。",
        "tags": ["防骗", "征信保护", "融资安全"],
        "read_min": 5,
        "updated": "2026-07-08",
        "body": [
            ("套路一:前置收费", "任何在放款前以'保证金''解冻费''疏通费'名义要你先付钱的,基本都是骗局。正规机构不收前置费。"),
            ("套路二:包装征信/流水", "承诺帮你'洗白征信''做高流水'的都涉嫌违法,一旦被查将影响更严重,切勿参与。"),
            ("套路三:AB 贷", "以你名义贷款却让第三方用款,你承担全部还款责任。凡是让你为他人'走个流程'的,坚决拒绝。"),
            ("套路四:绝对化承诺", "'秒批''必过''无视征信'等宣传违反监管规定,正规机构不会做此类承诺。"),
            ("套路五:阴阳费率", "只跟你说单月费率、日息,回避年化综合成本。签约前务必要求对方明确 IRR 口径年化成本。"),
            ("套路六:诱导多头借贷", "同时向多家机构申请、以贷养贷会推高负债率、拉低征信,反而更难获得正规低成本资金。"),
            ("提示", "本平台定位为融资信息中介,不放贷、不收前置费,所有合作机构均为持牌银行/机构。遇到可疑情况可在平台咨询核实。"),
        ],
    },
    {
        "id": "guide-credit-repair",
        "category": "融资科普",
        "title": "征信有瑕疵还能贷款吗?小微企业主的征信修复与增信思路",
        "summary": "逾期、查询过多、负债偏高怎么办?给出可落地的养征信与增信路径。",
        "tags": ["征信修复", "增信", "通过率"],
        "read_min": 4,
        "updated": "2026-06-20",
        "body": [
            ("先看征信问题类型", "当前逾期、历史逾期、硬查询过多、负债率偏高,处理优先级不同。当前逾期需最优先结清。"),
            ("养征信的正确姿势", "结清当前逾期后保持 6-24 个月零逾期;减少不必要的贷款审批硬查询;适度降低负债率与信用卡使用率。"),
            ("用增信弥补征信", "补充抵押物、提供稳定纳税/开票流水、引入担保、缩短借款期限或降低申请额度,都能提升通过率。"),
            ("分层匹配产品", "征信一般时,优先银税贷/信用贷;有设备厂房时走抵押贷;可在本平台按你的真实情况做 8 维风控打分,看清'为什么通过率低'并获得改善建议。"),
            ("提示", "征信修复没有捷径,任何'花钱铲单'都不可信。平台提供征信自查指引与增信建议,帮助你合规提升资质。"),
        ],
    },
]


def _extra() -> List[Dict]:
    raw = storage.get_setting("content_extra", "")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _disabled() -> List[str]:
    raw = storage.get_setting("content_disabled", "")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def list_articles(category: str = "", include_disabled: bool = False) -> List[Dict]:
    """列出文章摘要(不含正文),内置 + 自定义,按更新时间倒序。"""
    disabled = set(_disabled())
    items = [dict(a) for a in ARTICLES] + _extra()
    out = []
    for a in items:
        if not include_disabled and a["id"] in disabled:
            continue
        if category and a.get("category") != category:
            continue
        out.append({
            "id": a["id"],
            "category": a.get("category", "融资科普"),
            "title": a.get("title", ""),
            "summary": a.get("summary", ""),
            "tags": a.get("tags", []),
            "read_min": a.get("read_min", 3),
            "updated": a.get("updated", ""),
            "builtin": a.get("id", "").startswith(("guide-", "policy-", "avoid-")),
            "disabled": a["id"] in disabled,
        })
    out.sort(key=lambda x: x.get("updated", ""), reverse=True)
    return out


def get_article(article_id: str) -> Optional[Dict]:
    for a in ARTICLES + _extra():
        if a["id"] == article_id:
            body = a.get("body", [])
            norm = [{"h": h, "p": p} for h, p in body] if body and isinstance(body[0], (list, tuple)) else body
            return {**a, "body": norm}
    return None


def add_article(data: Dict) -> Dict:
    extras = _extra()
    title = (data.get("title") or "").strip()
    if not title:
        return {"ok": False, "error": "标题必填"}
    body_raw = data.get("body") or ""
    if isinstance(body_raw, str):
        paras = [p.strip() for p in body_raw.split("\n") if p.strip()]
        body = [(f"第 {i+1} 段", p) for i, p in enumerate(paras)] or [("正文", body_raw)]
    else:
        body = body_raw
    art = {
        "id": "art-" + uuid.uuid4().hex[:8],
        "category": data.get("category") if data.get("category") in CATEGORIES else "融资科普",
        "title": title[:80],
        "summary": (data.get("summary") or "").strip()[:160],
        "tags": [t.strip() for t in (data.get("tags") or []) if str(t).strip()][:6],
        "read_min": max(1, min(30, int(data.get("read_min", 3) or 3))),
        "updated": (data.get("updated") or "2026-07").strip()[:10],
        "body": body,
    }
    extras.append(art)
    storage.set_setting("content_extra", json.dumps(extras, ensure_ascii=False))
    return {"ok": True, "article": {"id": art["id"], "title": art["title"]}}


def set_disabled(article_id: str, disabled: bool) -> Dict:
    cur = set(_disabled())
    if disabled:
        cur.add(article_id)
    else:
        cur.discard(article_id)
    storage.set_setting("content_disabled", json.dumps(list(cur), ensure_ascii=False))
    return {"ok": True}


def delete_article(article_id: str) -> Dict:
    extras = [a for a in _extra() if a["id"] != article_id]
    storage.set_setting("content_extra", json.dumps(extras, ensure_ascii=False))
    return {"ok": True}


# ---------------- 留存运营:动态通知(LPR/政策/贴息到期) ----------------
def retention_notices() -> List[Dict]:
    """返回给前台消息中心的运营通知(LPR 基准、政策更新、贴息申报提醒)。"""
    import lpr_reference as lp
    notices = [
        {
            "id": "lpr-" + lp.LPR_UPDATED,
            "type": "利率提醒",
            "title": "LPR 利率基准提醒",
            "body": f"当前一年期 LPR {lp.LPR_1Y}%、五年期以上 {lp.LPR_5Y}%(自 {lp.LPR_UPDATED} 起)。你的贷款利率通常在 LPR 基础上加点,测算时可据此估算综合成本。",
        },
        {
            "id": "policy-refresh-2026-07",
            "type": "政策更新",
            "title": "2026 年 7 月贴息政策已更新",
            "body": "多地创业担保贷款贴息、技改贴息政策已刷新,建议到「隐藏贴息专区」按注册地重新匹配,避免错过申报窗口。",
        },
        {
            "id": "free-diagnosis-2026-07",
            "type": "活动",
            "title": "限时免费融资诊断",
            "body": "本月完成企业测算即可获得一次免费深度风控诊断,看清 8 维失分点与提额降息路径。",
        },
    ]
    return notices
