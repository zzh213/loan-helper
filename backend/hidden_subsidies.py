"""园区/区县「隐藏贴息」专区数据库与按地址匹配逻辑。

特点:收录通用大模型检索不到的园区、区县级非公开/小范围公示的贴息与补贴,
企业输入所在省/市/区县/园区即可解锁专属清单。数据为示意性整理,实际申报以
当地主管部门最新口径为准。可持续扩充。
"""
from typing import Dict, List

# 每条:province/city/district/park 任一关键词命中即解锁;industries 为空代表不限行业
HIDDEN_SUBSIDIES: List[Dict] = [
    {
        "id": "sh-zj-chip", "region": "上海·张江科学城",
        "keywords": ["上海", "浦东", "张江"],
        "name": "张江园区集成电路/生物医药专项贴息",
        "category": "园区贴息", "exclusive": True,
        "benefit": "园区内研发型企业贷款贴息上浮至 3%,最高 50 万元/年,叠加房租减免",
        "industries": ["科技", "制造业"],
        "apply_points": "向张江管委会产业促进处提交研发立项、贷款合同;名额按季度限额,非公开公示",
        "amount_max": 50, "rate_subsidy": 3.0,
    },
    {
        "id": "sz-nshan-soft", "region": "深圳·南山科技园",
        "keywords": ["深圳", "南山", "科技园", "粤海"],
        "name": "南山区软件企业研发贴息+上市奖励",
        "category": "区县奖补", "exclusive": True,
        "benefit": "软件/AI 企业贷款贴息 2%,研发投入超 100 万再奖 30 万;名额内部分配",
        "industries": ["科技"],
        "apply_points": "经南山区科技创新局白名单邀请申报,需双软认证或高企资质",
        "amount_max": 30, "rate_subsidy": 2.0,
    },
    {
        "id": "hz-yuhang-ecom", "region": "杭州·余杭未来科技城",
        "keywords": ["杭州", "余杭", "未来科技城", "临平"],
        "name": "余杭电商/直播基地贴息",
        "category": "园区贴息", "exclusive": True,
        "benefit": "入驻基地的电商企业贷款贴息 1.5%,GMV 达标再补仓储租金 20 万",
        "industries": ["批发零售", "服务业"],
        "apply_points": "入驻认定直播基地,提供 GMV 流水,向科技城财政科申报",
        "amount_max": 20, "rate_subsidy": 1.5,
    },
    {
        "id": "cd-gx-mfg", "region": "成都·高新区",
        "keywords": ["成都", "天府"],
        "name": "成都高新区智能制造技改隐性奖补",
        "category": "区县奖补", "exclusive": True,
        "benefit": "设备投资 200 万以上按 10% 事后奖补,贷款再贴息 1.5%",
        "industries": ["制造业"],
        "apply_points": "技改项目备案+验收,向高新区经信局定向窗口申报,不公开排名",
        "amount_max": 40, "rate_subsidy": 1.5,
    },
    {
        "id": "sz-county-agri", "region": "县域·乡村振兴园",
        "keywords": ["县", "镇", "乡", "农业园"],
        "name": "县域农业经营主体贷款全额贴息",
        "category": "县域专项", "exclusive": True,
        "benefit": "纳入名录的家庭农场/合作社 50 万内贷款财政全额贴息",
        "industries": ["农业"],
        "apply_points": "需当地农业农村局名录企业,村镇银行联合申报,窗口随农时不定期开放",
        "amount_max": 50, "rate_subsidy": 4.0,
    },
    {
        "id": "common-park-rent", "region": "各地·小微创业园",
        "keywords": ["园区", "孵化", "创业园", "产业园"],
        "name": "园区小微企业租金+贴息组合包",
        "category": "园区贴息", "exclusive": True,
        "benefit": "入驻园区前两年租金减半,贷款贴息 1%,仅向在园企业内部告知",
        "industries": [],
        "apply_points": "持园区租赁合同向管委会申报,名额有限先到先得",
        "amount_max": 15, "rate_subsidy": 1.0,
    },
    {
        "id": "bj-zgc-tech", "region": "北京·中关村",
        "keywords": ["北京", "海淀", "中关村", "朝阳"],
        "name": "中关村高新企业研发贷贴息",
        "category": "园区贴息", "exclusive": True,
        "benefit": "高企/专精特新研发贷贴息 2.5%,最高 40 万,叠加场地补贴",
        "industries": ["科技", "制造业"],
        "apply_points": "中关村管委会白名单邀约,需高企或专精特新资质,内部限额",
        "amount_max": 40, "rate_subsidy": 2.5,
    },
    {
        "id": "sz-jiangbei", "region": "苏州·工业园区",
        "keywords": ["苏州", "工业园", "园区", "昆山"],
        "name": "苏州工业园区先进制造贴息",
        "category": "区县奖补", "exclusive": True,
        "benefit": "智能制造设备投资奖补 8%,贷款贴息 2%,名额定向分配",
        "industries": ["制造业", "科技"],
        "apply_points": "园区经发委定向窗口,需项目备案+验收,不公开排名",
        "amount_max": 45, "rate_subsidy": 2.0,
    },
    {
        "id": "wh-optics", "region": "武汉·光谷",
        "keywords": ["武汉", "东湖", "光谷", "洪山"],
        "name": "光谷光电子/生物医药贴息",
        "category": "园区贴息", "exclusive": True,
        "benefit": "光电子、生物医药企业贷款贴息 2%,最高 35 万,叠加人才补贴",
        "industries": ["科技", "制造业"],
        "apply_points": "光谷管委会产业处定向申报,需入库企业",
        "amount_max": 35, "rate_subsidy": 2.0,
    },
    {
        "id": "cq-liangjiang", "region": "重庆·两江新区",
        "keywords": ["重庆", "两江", "渝北"],
        "name": "两江新区中小企业稳产贴息",
        "category": "区县奖补", "exclusive": True,
        "benefit": "汽车/电子配套企业流贷贴息 1.5%,稳岗再补 15 万",
        "industries": ["制造业", "物流"],
        "apply_points": "两江新区经信局名录企业,人社联合申报",
        "amount_max": 25, "rate_subsidy": 1.5,
    },
    {
        "id": "xa-hightech", "region": "西安·高新区",
        "keywords": ["西安", "雁塔"],
        "name": "西安高新区硬科技专项贴息",
        "category": "园区贴息", "exclusive": True,
        "benefit": "硬科技企业研发贷贴息 2%,最高 30 万,叠加流片补助",
        "industries": ["科技"],
        "apply_points": "高新区科技局白名单,需硬科技认证,季度限额",
        "amount_max": 30, "rate_subsidy": 2.0,
    },
    {
        "id": "gz-dongguan", "region": "广东·东莞松山湖",
        "keywords": ["东莞", "松山湖"], "name": "松山湖智能制造贴息",
        "category": "园区贴息", "exclusive": True,
        "benefit": "智能终端/机器人企业设备贷贴息 2%,最高 35 万,叠加技改奖补",
        "industries": ["制造业", "科技"],
        "apply_points": "松山湖管委会定向窗口,需高企或专精特新", "amount_max": 35, "rate_subsidy": 2.0,
    },
    {
        "id": "fs-shunde", "region": "广东·佛山顺德", "keywords": ["佛山", "顺德"],
        "name": "顺德家电产业带流贷贴息", "category": "区县奖补", "exclusive": True,
        "benefit": "家电制造企业流贷贴息 1.5%,稳岗再补 20 万", "industries": ["制造业"],
        "apply_points": "顺德经促局名录企业内部分配", "amount_max": 28, "rate_subsidy": 1.5,
    },
    {
        "id": "nj-jiangbei", "region": "江苏·南京江北新区", "keywords": ["南京", "江北"],
        "name": "江北新区集成电路/医药贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "芯片、生物医药研发贷贴息 2.5%,最高 45 万", "industries": ["科技", "制造业"],
        "apply_points": "江北新区科创局白名单邀约", "amount_max": 45, "rate_subsidy": 2.5,
    },
    {
        "id": "nb-beilun", "region": "浙江·宁波北仑", "keywords": ["宁波", "北仑"],
        "name": "宁波港口外贸企业贴息", "category": "区县奖补", "exclusive": True,
        "benefit": "外贸制造企业流贷贴息 1.5%,出口达标补 18 万", "industries": ["制造业", "物流", "批发零售"],
        "apply_points": "北仑商务局名录企业申报", "amount_max": 22, "rate_subsidy": 1.5,
    },
    {
        "id": "qd-laoshan", "region": "山东·青岛崂山", "keywords": ["青岛", "崂山"],
        "name": "青岛崂山虚拟现实/海洋科技贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "VR/海洋科技研发贷贴息 2%,最高 30 万", "industries": ["科技"],
        "apply_points": "崂山区科技局白名单", "amount_max": 30, "rate_subsidy": 2.0,
    },
    {
        "id": "hf-gaoxin", "region": "安徽·合肥高新", "keywords": ["合肥", "蜀山"],
        "name": "合肥高新区芯屏汽合贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "集成电路/新能源汽车研发贷贴息 2.5%,最高 40 万", "industries": ["科技", "制造业"],
        "apply_points": "高新区管委会定向申报", "amount_max": 40, "rate_subsidy": 2.5,
    },
    {
        "id": "cs-yuelu", "region": "湖南·长沙岳麓", "keywords": ["长沙", "岳麓", "湘江"],
        "name": "长沙湘江新区工程机械贴息", "category": "区县奖补", "exclusive": True,
        "benefit": "工程机械配套企业贴息 1.5%,最高 25 万", "industries": ["制造业"],
        "apply_points": "湘江新区经发局名录企业", "amount_max": 25, "rate_subsidy": 1.5,
    },
    {
        "id": "zz-zhengdong", "region": "河南·郑州航空港", "keywords": ["郑州", "航空港", "南阳", "洛阳"],
        "name": "郑州航空港智能终端贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "电子信息企业流贷贴息 1.8%,最高 28 万", "industries": ["制造业", "物流"],
        "apply_points": "航空港实验区管委会申报", "amount_max": 28, "rate_subsidy": 1.8,
    },
    {
        "id": "xm-huoju", "region": "福建·厦门火炬", "keywords": ["厦门", "火炬", "泉州", "福州"],
        "name": "厦门火炬高新区两岸创业贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "科技/台企研发贷贴息 2%,最高 32 万", "industries": ["科技", "制造业"],
        "apply_points": "火炬管委会白名单,台企优先", "amount_max": 32, "rate_subsidy": 2.0,
    },
    {
        "id": "sy-tiexi", "region": "辽宁·沈阳铁西", "keywords": ["沈阳", "铁西", "大连"],
        "name": "沈阳铁西装备制造振兴贴息", "category": "区县奖补", "exclusive": True,
        "benefit": "装备制造技改贴息 2%,最高 30 万,东北振兴叠加", "industries": ["制造业"],
        "apply_points": "铁西区工信局名录企业", "amount_max": 30, "rate_subsidy": 2.0,
    },
    {
        "id": "km-dianchi", "region": "云南·昆明滇中", "keywords": ["昆明", "曲靖", "滇中"],
        "name": "昆明滇中新区高原特色农业贴息", "category": "县域专项", "exclusive": True,
        "benefit": "特色农业加工企业全额贴息,最高 50 万", "industries": ["农业"],
        "apply_points": "滇中新区农业农村部门名录", "amount_max": 50, "rate_subsidy": 3.5,
    },
    {
        "id": "nn-wuxiang", "region": "广西·南宁五象", "keywords": ["南宁", "五象", "柳州", "桂林"],
        "name": "南宁五象新区面向东盟外贸贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "外贸/物流企业贴息 1.8%,最高 26 万", "industries": ["物流", "批发零售"],
        "apply_points": "五象新区商务局申报,东盟贸易优先", "amount_max": 26, "rate_subsidy": 1.8,
    },
    {
        "id": "my-keji", "region": "四川·绵阳科技城", "keywords": ["绵阳", "科技城"],
        "name": "绵阳科技城军民融合研发贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "电子信息/军民融合研发贷贴息 2%,最高 32 万", "industries": ["科技", "制造业"],
        "apply_points": "科技城管委会白名单申报", "amount_max": 32, "rate_subsidy": 2.0,
    },
    {
        "id": "yc-gaoxin", "region": "湖北·宜昌", "keywords": ["宜昌", "襄阳"],
        "name": "宜昌精细化工/装备贴息", "category": "区县奖补", "exclusive": True,
        "benefit": "化工、装备企业技改贴息 1.8%,最高 28 万", "industries": ["制造业"],
        "apply_points": "市经信局名录企业申报", "amount_max": 28, "rate_subsidy": 1.8,
    },
    {
        "id": "ts-caofeidian", "region": "河北·唐山", "keywords": ["唐山", "曹妃甸", "保定", "石家庄"],
        "name": "唐山钢铁配套绿色转型贴息", "category": "区县奖补", "exclusive": True,
        "benefit": "钢铁配套绿色技改贴息 2%,最高 30 万", "industries": ["制造业"],
        "apply_points": "市工信局名录企业,京津冀协同优先", "amount_max": 30, "rate_subsidy": 2.0,
    },
    {
        "id": "bj-baoji", "region": "陕西·宝鸡", "keywords": ["宝鸡", "咸阳"],
        "name": "宝鸡钛产业集群贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "钛及新材料企业流贷贴息 1.8%,最高 26 万", "industries": ["制造业"],
        "apply_points": "高新区管委会名录企业", "amount_max": 26, "rate_subsidy": 1.8,
    },
    {
        "id": "nc-ganzhou", "region": "江西·赣州", "keywords": ["赣州", "南昌", "九江"],
        "name": "赣州稀土/家具产业带贴息", "category": "区县奖补", "exclusive": True,
        "benefit": "稀土深加工、家具企业贴息 1.8%,最高 25 万", "industries": ["制造业"],
        "apply_points": "市工信局名录企业内部分配", "amount_max": 25, "rate_subsidy": 1.8,
    },
    {
        "id": "ty-zonghe", "region": "山西·太原", "keywords": ["太原", "大同"],
        "name": "太原能源革命综改区贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "新能源/煤化工转型贷贴息 2%,最高 30 万", "industries": ["制造业", "科技"],
        "apply_points": "综改示范区管委会申报", "amount_max": 30, "rate_subsidy": 2.0,
    },
    {
        "id": "gy-dashuju", "region": "贵州·贵阳", "keywords": ["贵阳", "遵义"],
        "name": "贵阳大数据企业研发贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "大数据/算力企业贴息 2.5%,最高 35 万", "industries": ["科技"],
        "apply_points": "高新区大数据局白名单", "amount_max": 35, "rate_subsidy": 2.5,
    },
    {
        "id": "hrb-bing", "region": "黑龙江·哈尔滨", "keywords": ["哈尔滨", "大庆"],
        "name": "哈尔滨装备/食品工业振兴贴息", "category": "区县奖补", "exclusive": True,
        "benefit": "装备制造、绿色食品贴息 2%,最高 28 万,东北振兴叠加", "industries": ["制造业", "农业"],
        "apply_points": "市工信局名录企业", "amount_max": 28, "rate_subsidy": 2.0,
    },
    {
        "id": "cc-qiche", "region": "吉林·长春", "keywords": ["长春", "吉林"],
        "name": "长春汽车产业配套贴息", "category": "区县奖补", "exclusive": True,
        "benefit": "汽车零部件企业流贷贴息 1.8%,最高 30 万", "industries": ["制造业"],
        "apply_points": "汽开区经发局名录企业", "amount_max": 30, "rate_subsidy": 1.8,
    },
    {
        "id": "hk-zimao", "region": "海南·海口", "keywords": ["海口", "三亚", "海南"],
        "name": "海南自贸港企业贴息+免税扶持", "category": "省级专项", "exclusive": True,
        "benefit": "鼓励类企业贴息 2%,叠加自贸港所得税优惠,最高 40 万", "industries": [],
        "apply_points": "自贸港管理部门申报,需鼓励类目录企业", "amount_max": 40, "rate_subsidy": 2.0,
    },
    {
        "id": "lz-lanbai", "region": "甘肃·兰州", "keywords": ["兰州", "天水"],
        "name": "兰州新区化工/装备贴息", "category": "园区贴息", "exclusive": True,
        "benefit": "石化、装备企业贴息 1.8%,最高 25 万", "industries": ["制造业"],
        "apply_points": "兰州新区管委会名录企业", "amount_max": 25, "rate_subsidy": 1.8,
    },
]

# 省级通用兜底:任一省/直辖市/自治区命中即解锁,确保全国覆盖
PROVINCE_KEYWORDS = [
    "北京", "天津", "上海", "重庆", "广东", "深圳", "广州", "江苏", "苏州", "南京",
    "浙江", "杭州", "宁波", "山东", "青岛", "济南", "四川", "成都", "湖北", "武汉",
    "湖南", "长沙", "河南", "郑州", "河北", "石家庄", "福建", "厦门", "福州", "安徽",
    "合肥", "陕西", "西安", "辽宁", "沈阳", "大连", "江西", "南昌", "山西", "太原",
    "云南", "昆明", "广西", "南宁", "贵州", "贵阳", "黑龙江", "哈尔滨", "吉林", "长春",
    "甘肃", "兰州", "海南", "海口", "内蒙古", "呼和浩特", "新疆", "乌鲁木齐", "宁夏",
    "银川", "青海", "西宁", "西藏", "拉萨", "香港", "澳门", "台湾", "县", "市", "区",
]

PROVINCE_FALLBACK = {
    "id": "prov-puhui", "region": "本省·普惠小微",
    "name": "省级普惠小微贷款贴息+创业担保贴息",
    "category": "省级专项", "exclusive": True,
    "benefit": "本省小微/个体贷款贴息 1%-2%,创业担保贷款最高 50 万财政贴息;名额按区县分配,非全网公示",
    "industries": [],
    "apply_points": "向所在区县政务服务中心/人社局窗口申报,需营业执照+贷款合同,窗口期不定期开放",
    "amount_max": 50, "rate_subsidy": 2.0,
}


def match_hidden(address: str, industry: str = "") -> List[Dict]:
    """按地址关键词解锁隐藏贴息;行业不限或匹配时返回。无具体命中则给省级兜底。"""
    addr = (address or "").strip()
    out = []
    for s in HIDDEN_SUBSIDIES:
        if not any(k in addr for k in s["keywords"]):
            continue
        if s["industries"] and industry and industry not in s["industries"]:
            continue
        out.append({k: v for k, v in s.items() if k != "keywords"})
    if not out and addr and any(k in addr for k in PROVINCE_KEYWORDS):
        item = dict(PROVINCE_FALLBACK)
        item["region"] = f"{addr}·普惠小微"
        out.append(item)
    return out
