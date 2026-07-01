"""智能助手:优先 Azure OpenAI,其次本地 Ollama,再次通义千问云端,最后内置知识库降级。

四种工作模式(自动按顺序选用,无需手动切换):
  1) Azure OpenAI —— 配置后效果最佳,需以下环境变量(推荐企业部署)
       AZURE_OPENAI_ENDPOINT     如 https://xxx.openai.azure.com
       AZURE_OPENAI_API_KEY      Azure 资源密钥
       AZURE_OPENAI_DEPLOYMENT   部署名(deployment name)
       AZURE_OPENAI_API_VERSION  接口版本,默认 2024-08-01-preview
  2) 本地大模型 Ollama —— 免费、无需 API Key、可离线自由对话
       需先安装 Ollama 并拉取模型,例如: ollama pull qwen2.5
  3) 通义千问云端 —— 需配置环境变量 DASHSCOPE_API_KEY
  4) 内置关键词知识库 —— 以上都不可用时的兜底

可选环境变量:
  OLLAMA_URL        Ollama 服务地址,默认 http://127.0.0.1:11434
  OLLAMA_MODEL      本地模型名,默认 qwen2.5
  DASHSCOPE_API_KEY 通义千问 API Key(可选)
  QWEN_MODEL        云端模型名,默认 qwen-plus
"""
import json
import os
from typing import Iterator, List

import httpx

DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL = os.environ.get("QWEN_MODEL", "qwen-plus")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5")

AZURE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
AZURE_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
AZURE_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
AZURE_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

SYSTEM_PROMPT = (
    "你是「小微贷管家」,一位博学、亲切、有耐心的全能 AI 助手。"
    "你尤其擅长经济与金融领域(贷款融资、征信、利率、投资理财、保险、税务、宏观经济、"
    "财务知识、风险防范、防范诈骗等),能用通俗易懂的中文把专业问题讲清楚。"
    "同时,你也是一位无所不谈的生活助手:无论用户问的是经济金融,还是日常生活、健康、"
    "学习、工作、旅行、美食、科技、情感、写作、闲聊等任何话题,你都应当尽力提供有帮助、"
    "准确、友善的回答,不要拒绝或刻意把话题强行拉回贷款。"
    "回答要点:1) 简洁实用,条理清晰,适当分点;2) 语气自然亲切,像朋友一样;"
    "3) 涉及金融具体额度/利率/收益时,提醒仅供参考,投资有风险、贷款以金融机构实际审批为准;"
    "4) 涉及医疗、法律、重大投资等专业决策时,建议用户咨询相应的专业人士;"
    "5) 遇到贷款诈骗类问题,提醒'正规贷款放款前不收费',警惕'无抵押秒批、包过'等骗局;"
    "6) 如果用户咨询的是企业融资需求,可顺势告诉他本平台的'智能匹配'页能填写企业情况、"
    "一键获取个性化贷款方案与可申报补贴,但这只是友好建议,不要喧宾夺主。"
)

# ---------------- 内置知识库(降级回答) ----------------
KNOWLEDGE = [
    {
        "keywords": ["征信", "信用记录", "逾期", "黑名单"],
        "answer": (
            "关于征信:\n"
            "1. 征信是银行审批贷款的核心依据,记录你的借贷与还款情况。\n"
            "2. 当前有逾期会显著影响审批和额度,建议先结清逾期再申请。\n"
            "3. 征信修复需要时间,保持按时还款、降低负债率,6 个月-2 年可逐步改善。\n"
            "4. 企业贷款会同时看企业征信和法人个人征信。\n"
            "提示:可在'智能匹配'页填写真实征信状况,系统会据此推荐合适产品。"
        ),
    },
    {
        "keywords": ["利率", "利息", "年化", "多少钱", "费用", "成本"],
        "answer": (
            "关于贷款利率:\n"
            "1. 年化利率因产品而异:普惠/抵押类约 3%-6%,银税信用贷约 4%-7%,"
            "互联网流水贷约 7%-15%,小贷应急约 12%-23%。\n"
            "2. 征信越好、有抵押或纳税记录,利率越低。\n"
            "3. 注意区分'年化利率'和'月费率',月费率×12 才是大致年化。\n"
            "4. 正规贷款不会在放款前收取手续费、保证金。\n"
            "以上为参考区间,实际以金融机构审批为准。"
        ),
    },
    {
        "keywords": ["抵押", "担保", "房产", "质押"],
        "answer": (
            "关于抵押担保:\n"
            "1. 有房产、设备等抵押物可申请大额、低息、长期限的经营贷,通常额度可达抵押物估值的 6-7 成。\n"
            "2. 无抵押也可申请信用贷、银税互动贷、普惠贷,但额度相对较低。\n"
            "3. 担保方式还包括保证担保(第三方/担保公司)、知识产权质押(科技企业)。\n"
            "4. 抵押贷需办理抵押登记,放款周期相对较长(10-20 个工作日)。"
        ),
    },
    {
        "keywords": ["流程", "怎么申请", "如何申请", "需要什么", "材料", "条件"],
        "answer": (
            "贷款申请一般流程:\n"
            "1. 准备材料:营业执照、近 1-2 年财务/流水、纳税记录、法人身份证、(如有)抵押物证明。\n"
            "2. 选择产品:根据资质匹配合适的银行或产品。\n"
            "3. 提交申请并授权征信查询。\n"
            "4. 银行审批(评估额度、利率)。\n"
            "5. 签约放款。\n"
            "建议先在'智能匹配'页填写企业情况,系统会给出最优方案和所需条件。"
        ),
    },
    {
        "keywords": ["普惠", "政策", "补贴", "贴息", "扶持"],
        "answer": (
            "关于普惠金融与补贴:\n"
            "1. 普惠小微贷款享受国家政策支持,利率较低,部分地区还有财政贴息(1%-2%)。\n"
            "2. 常见扶持:创业担保贷款贴息、科技型中小企业研发补助、稳岗扩岗补贴、"
            "制造业技改奖补、小微企业税费减免等。\n"
            "3. 申报渠道一般为当地政务服务中心、人社局、科技局、税务局等。\n"
            "在'智能匹配'页填写企业信息,系统会自动匹配你可申报的扶持政策。"
        ),
    },
    {
        "keywords": ["纳税", "银税", "开票", "发票"],
        "answer": (
            "关于纳税与银税互动:\n"
            "1. 连续、规范的纳税记录可以'换'贷款额度,这就是'银税互动'信用贷。\n"
            "2. 纳税信用等级越高(A/B 级),可获额度越高、利率越低。\n"
            "3. 稳定的开票流水能证明经营真实性,有助于提升信用评估。\n"
            "4. 建议规范记账报税,长期看能显著改善融资条件。"
        ),
    },
    {
        "keywords": ["额度", "能贷多少", "贷多少", "上限"],
        "answer": (
            "关于可贷额度:\n"
            "1. 信用贷额度通常参考年营业额的 20%-40%。\n"
            "2. 抵押贷额度参考抵押物估值的 60%-70%。\n"
            "3. 征信好、经营年限长、有纳税记录会提高额度。\n"
            "4. 建议贷款额度控制在年营收的 50% 以内,避免杠杆过高。\n"
            "在'智能匹配'页填写信息可获得精确的额度估算。"
        ),
    },
    {
        "keywords": ["骗局", "诈骗", "被骗", "套路", "安全", "中介"],
        "answer": (
            "防范贷款诈骗,请牢记:\n"
            "1. 正规贷款放款前绝不会收取'手续费、保证金、解冻费、刷流水费'。\n"
            "2. 警惕'无抵押、无征信、秒批、包过'等夸大宣传。\n"
            "3. 不要轻信陌生来电、短信链接,认准持牌金融机构。\n"
            "4. 不向他人透露银行卡密码、短信验证码。\n"
            "5. 签合同前看清利率、费用、还款方式等条款。\n"
            "如遇可疑情况,及时拨打 96110 反诈专线。"
        ),
    },
    {
        "keywords": ["理财", "投资", "基金", "股票", "存钱", "怎么存", "余额宝", "定投"],
        "answer": (
            "关于个人理财投资的几点通用建议:\n"
            "1. 先建立 3-6 个月生活费的应急储备金,再考虑投资。\n"
            "2. 遵循'不要把鸡蛋放在一个篮子里',分散配置,降低风险。\n"
            "3. 风险与收益成正比:存款/货币基金最稳但收益低,股票/股票基金波动大。\n"
            "4. 普通人可考虑指数基金定投,长期、纪律性投入以平滑波动。\n"
            "5. 远离'保本高息''稳赚不赔'的宣传,这类多为骗局。\n"
            "投资有风险,入市需谨慎,以上仅为通用知识,不构成投资建议。"
        ),
    },
    {
        "keywords": ["保险", "社保", "医保", "重疾", "意外险", "养老"],
        "answer": (
            "关于保险的通用思路:\n"
            "1. 先把社保(医保、养老)交齐,这是最基础的保障。\n"
            "2. 商业保险配置顺序一般是:意外险→重疾险→医疗险→寿险,最后才是理财型。\n"
            "3. 先保'大人(家庭经济支柱)'再保孩子,先保障后理财。\n"
            "4. 投保前如实告知健康状况,看清保障范围与免责条款。\n"
            "具体方案建议结合家庭情况咨询专业的保险顾问。"
        ),
    },
    {
        "keywords": ["通货膨胀", "通胀", "gdp", "经济", "汇率", "降息", "加息", "宏观"],
        "answer": (
            "一些常见的经济概念:\n"
            "1. 通货膨胀:物价普遍上涨、货币购买力下降,温和通胀是经济正常现象。\n"
            "2. GDP:国内生产总值,衡量一个经济体的总产出与景气程度。\n"
            "3. 加息/降息:央行调节资金价格的手段——加息抑制过热、降息刺激经济。\n"
            "4. 汇率:一国货币兑换他国货币的价格,影响进出口与跨境投资。\n"
            "想了解某个具体概念,告诉我,我可以展开讲讲~"
        ),
    },
    {
        "keywords": ["还款", "月供", "提前还款", "等额本息", "先息后本"],
        "answer": (
            "关于还款方式:\n"
            "1. 等额本息:每月还款额固定,适合现金流稳定的企业。\n"
            "2. 先息后本:平时只还利息,到期还本,适合短期周转。\n"
            "3. 随借随还:按实际用款天数计息,灵活但需注意综合成本。\n"
            "4. 提前还款前确认是否有违约金。\n"
            "建议根据经营回款周期选择还款方式,预留 3 个月月供作为安全垫。"
        ),
    },
]

GREETING = (
    "您好!我是您的智能助手「小微贷管家」🤝\n"
    "别看名字带'贷',其实我什么都能聊~ 经济金融(贷款、理财、投资、保险、税务、宏观经济)"
    "是我的强项,日常生活、学习工作、健康旅行、闲聊解闷也都欢迎随便问。\n"
    "如果你是企业主想融资,也可以到'智能匹配'页填写企业情况,我帮你算出专属贷款方案~"
)


def _fallback_answer(message: str) -> str:
    if any(w in message for w in ["你好", "您好", "hi", "hello", "在吗", "你是谁", "你能做什么", "你会什么"]):
        return GREETING
    for item in KNOWLEDGE:
        if any(k in message for k in item["keywords"]):
            return item["answer"]
    return (
        "这个问题我很乐意和你聊聊~ 不过我目前没有连接在线大模型,"
        "暂时无法对开放性问题给出最完整的回答。你可以:\n"
        "1. 换个更具体的说法再问我一次;\n"
        "2. 金融理财类问题我最在行——比如'征信不好能贷款吗''怎么开始定投''保险怎么配置''什么是通货膨胀'等;\n"
        "3. 如果是企业融资需求,到'智能匹配'页填写企业信息,我能直接帮你测算贷款方案与可申报补贴。\n"
        "(小提示:配置在线大模型后,我就能回答几乎任何问题啦~)"
    )


def _ollama_model_ready() -> bool:
    """检测本地 Ollama 是否在运行且已拉取可用模型。"""
    try:
        resp = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=1.5)
        if resp.status_code != 200:
            return False
        models = [m.get("name", "") for m in resp.json().get("models", [])]
        if not models:
            return False
        # 精确或前缀匹配(qwen2.5 可匹配 qwen2.5:latest 等)
        return any(name == OLLAMA_MODEL or name.startswith(OLLAMA_MODEL + ":")
                   for name in models)
    except Exception:
        return False


def active_provider() -> str:
    """返回当前生效的对话后端: 'azure' / 'ollama' / 'dashscope' / 'fallback'。"""
    if AZURE_ENDPOINT and AZURE_API_KEY and AZURE_DEPLOYMENT:
        return "azure"
    if _ollama_model_ready():
        return "ollama"
    if os.environ.get("DASHSCOPE_API_KEY"):
        return "dashscope"
    return "fallback"


def is_llm_enabled() -> bool:
    return active_provider() != "fallback"


def _build_messages(message: str, history: List[dict]) -> List[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-10:]:
        role = h.get("role")
        content = h.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})
    return messages


def _stream_ollama(message: str, history: List[dict]) -> Iterator[str]:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": _build_messages(message, history),
        "stream": True,
        "options": {"temperature": 0.7},
    }
    got_any = False
    try:
        with httpx.stream("POST", f"{OLLAMA_URL}/api/chat", json=payload,
                          timeout=120.0) as resp:
            if resp.status_code != 200:
                resp.read()
                yield _fallback_answer(message)
                return
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                delta = obj.get("message", {}).get("content", "")
                if delta:
                    got_any = True
                    yield delta
                if obj.get("done"):
                    break
    except Exception:
        if not got_any:
            yield _fallback_answer(message)
        return
    if not got_any:
        yield _fallback_answer(message)


def _stream_dashscope(message: str, history: List[dict]) -> Iterator[str]:
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    payload = {"model": MODEL, "messages": _build_messages(message, history),
               "stream": True, "temperature": 0.7}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    got_any = False
    try:
        with httpx.stream("POST", DASHSCOPE_URL, json=payload, headers=headers,
                          timeout=60.0) as resp:
            if resp.status_code != 200:
                resp.read()
                yield _fallback_answer(message)
                return
            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith("data:"):
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        delta = obj["choices"][0]["delta"].get("content", "")
                        if delta:
                            got_any = True
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
    except Exception:
        if not got_any:
            yield _fallback_answer(message)
        return
    if not got_any:
        yield _fallback_answer(message)


def _stream_azure(message: str, history: List[dict]) -> Iterator[str]:
    url = (f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT}"
           f"/chat/completions?api-version={AZURE_API_VERSION}")
    payload = {"messages": _build_messages(message, history),
               "stream": True, "temperature": 0.7}
    headers = {"api-key": AZURE_API_KEY, "Content-Type": "application/json"}
    got_any = False
    try:
        with httpx.stream("POST", url, json=payload, headers=headers,
                          timeout=60.0) as resp:
            if resp.status_code != 200:
                resp.read()
                yield _fallback_answer(message)
                return
            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith("data:"):
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        choices = obj.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {}).get("content", "")
                        if delta:
                            got_any = True
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
    except Exception:
        if not got_any:
            yield _fallback_answer(message)
        return
    if not got_any:
        yield _fallback_answer(message)


def stream_reply(message: str, history: List[dict]) -> Iterator[str]:
    """生成回复文本块(生成器)。按 Azure → 本地Ollama → 通义千问 → 知识库 顺序降级。"""
    provider = active_provider()
    if provider == "azure":
        yield from _stream_azure(message, history)
    elif provider == "ollama":
        yield from _stream_ollama(message, history)
    elif provider == "dashscope":
        yield from _stream_dashscope(message, history)
    else:
        yield _fallback_answer(message)


def complete(prompt: str, system: str = "", max_tokens: int = 64) -> str:
    """非流式补全:用于短任务(如行业分类)。无可用大模型或失败时返回空串。"""
    provider = active_provider()
    if provider == "fallback":
        return ""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        if provider == "azure":
            url = (f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT}"
                   f"/chat/completions?api-version={AZURE_API_VERSION}")
            payload = {"messages": messages, "temperature": 0, "max_tokens": max_tokens}
            headers = {"api-key": AZURE_API_KEY, "Content-Type": "application/json"}
            resp = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        elif provider == "ollama":
            payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False,
                       "options": {"temperature": 0}}
            resp = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60.0)
            if resp.status_code == 200:
                return (resp.json().get("message", {}).get("content", "") or "").strip()
            return ""
        else:  # dashscope
            payload = {"model": MODEL, "messages": messages, "stream": False,
                       "temperature": 0, "max_tokens": max_tokens}
            headers = {"Authorization": f"Bearer {os.environ.get('DASHSCOPE_API_KEY')}",
                       "Content-Type": "application/json"}
            resp = httpx.post(DASHSCOPE_URL, json=payload, headers=headers, timeout=30.0)
        if resp.status_code != 200:
            return ""
        obj = resp.json()
        return (obj["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        return ""
