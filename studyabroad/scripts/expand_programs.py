#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量扩充 programs.json：录入热门校真实硕士项目名（含「经济与金融」这类具体项目）。
分数线为基于公开招生信息与往年中国大陆申请经验的参考线，非官方保证（meta.disclaimer 已说明）。
重复运行安全：按 id 去重，不会重复插入。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "programs.json")

data = json.load(open(PATH, encoding="utf-8"))
programs = data["programs"]
existing_ids = {p["id"] for p in programs}
existing_pairs = {(p["university"], p["program"]) for p in programs}


def req(avg985, avg211, avgsy, avgsf, avghb, io=6.5, isub=6.0, gre=None, bg="", notes=""):
    return {
        "avgByTier": {
            "985": avg985, "211": avg211, "双一流": avgsy,
            "双非": avgsf, "海本/中外合作": avghb,
        },
        "ielts": {"overall": io, "sub": isub},
        "gre": gre,
        "background": bg,
        "notes": notes,
    }


TUI = {
    "英国": "约 25–38 万元 / 1年",
    "中国香港": "约 14–28 万元 / 1年",
    "新加坡": "约 18–32 万元 / 1–1.5年",
    "澳大利亚": "约 20–35 万元 / 1.5–2年",
    "美国": "约 35–60 万元 / 1–2年",
}
DUR = {"英国": "1 年", "中国香港": "1 年", "新加坡": "1–1.5 年", "澳大利亚": "1.5–2 年", "美国": "1–2 年"}
TL = {
    "英国": "每年 9–10 月开放，滚动录取先到先得，建议 10–12 月递交",
    "中国香港": "每年 9 月开放，多轮截止，建议首轮（10–12 月）递交",
    "新加坡": "每年 10–11 月开放，建议次年 1–2 月前递交",
    "澳大利亚": "多为两次入学（2 月 / 7 月），常年滚动审理",
    "美国": "每年 9 月开放，截止 12 月–次年 1 月，部分有早申轮次",
}

NEW = [
    # ===================== 英国 · 金融/经济/商科集群 =====================
    ("uk-lse-fin", "英国", "伦敦政治经济学院 LSE", 50, "Finance MSc", "金融",
     req(85, 87, 88, 90, 80, 7.0, 6.5, None, "需金融/经济/数理等量化背景", "LSE 金融极卷，偏好 985/海本 + 量化成绩突出 + GMAT 700+")),
    ("uk-lse-finecon", "英国", "伦敦政治经济学院 LSE", 50, "Finance and Economics MSc", "金融",
     req(85, 87, 88, 90, 80, 7.0, 6.5, None, "需扎实经济学与数学/计量背景", "经济与金融交叉项目，看重微观/计量/数学课程成绩")),
    ("uk-lse-econ", "英国", "伦敦政治经济学院 LSE", 50, "Economics MSc", "经济学",
     req(85, 88, 89, 90, 80, 7.0, 6.5, None, "需经济学本科 + 强数学（高数/线代/概率）", "顶尖经济项目，常需 GRE Quant 高分")),
    ("uk-lse-accfin", "英国", "伦敦政治经济学院 LSE", 50, "Accounting and Finance MSc", "会计",
     req(84, 86, 88, 89, 79, 7.0, 6.5, None, "需会计/金融/经济相关背景", "会计与金融方向，竞争激烈")),
    ("uk-lse-mgmt", "英国", "伦敦政治经济学院 LSE", 50, "Management MSc", "管理学/商科",
     req(83, 85, 87, 88, 78, 7.0, 6.5, None, "商科或社科背景均可", "")),
    ("uk-ic-fin", "英国", "帝国理工学院", 2, "Finance MSc", "金融",
     req(83, 85, 87, 88, 78, 7.0, 6.5, None, "需量化/商科背景", "帝国商学院金融，偏好量化能力强者")),
    ("uk-ic-finml", "英国", "帝国理工学院", 2, "Financial Technology MSc", "金融工程",
     req(83, 85, 87, 88, 78, 7.0, 6.5, None, "需编程/数理/金融背景", "FinTech，重视 Python/统计")),
    ("uk-ic-rmfe", "英国", "帝国理工学院", 2, "Risk Management & Financial Engineering MSc", "金融工程",
     req(84, 86, 88, 89, 79, 7.0, 6.5, None, "需强数理与编程背景", "RMFE 偏量化金融，建议有 GRE")),
    ("uk-ic-iwm", "英国", "帝国理工学院", 2, "Investment & Wealth Management MSc", "金融",
     req(83, 85, 87, 88, 78, 7.0, 6.5, None, "需金融/经济/数理背景", "")),
    ("uk-ic-econbus", "英国", "帝国理工学院", 2, "Economics & Strategy for Business MSc", "经济学",
     req(82, 84, 86, 88, 78, 7.0, 6.5, None, "需经济/商科 + 数学背景", "")),
    ("uk-ucl-econ", "英国", "伦敦大学学院 UCL", 9, "Economics MSc", "经济学",
     req(83, 85, 87, 88, 78, 7.0, 6.5, None, "需经济学本科 + 强数学", "UCL 经济偏理论与计量")),
    ("uk-ucl-fin", "英国", "伦敦大学学院 UCL", 9, "Finance MSc", "金融",
     req(83, 85, 87, 88, 78, 7.0, 6.5, None, "需量化/金融/经济背景", "")),
    ("uk-ucl-mgmt", "英国", "伦敦大学学院 UCL", 9, "Management MSc", "管理学/商科",
     req(82, 84, 86, 88, 78, 6.5, 6.0, None, "应届/转专业友好", "UCL 管理学院，背景多元")),
    ("uk-ucl-ba", "英国", "伦敦大学学院 UCL", 9, "Business Analytics MSc", "商业分析",
     req(83, 85, 87, 88, 78, 6.5, 6.0, None, "需数理/编程基础", "")),
    ("uk-warwick-econ", "英国", "华威大学", 67, "Economics MSc", "经济学",
     req(82, 84, 86, 88, 78, 7.0, 6.0, None, "需经济 + 数学/计量背景", "WBS/经济系，量化要求高")),
    ("uk-warwick-fin", "英国", "华威大学", 67, "Finance MSc", "金融",
     req(82, 85, 87, 88, 78, 7.0, 6.5, None, "需量化背景", "WBS 金融，认可院校 list")),
    ("uk-warwick-finecon2", "英国", "华威大学", 67, "Finance and Economics MSc", "金融",
     req(83, 85, 87, 88, 78, 7.0, 6.5, None, "需经济 + 数理背景", "经济与金融交叉，WBS list 控制严格")),
    ("uk-warwick-ba", "英国", "华威大学", 67, "Business Analytics MSc", "商业分析",
     req(82, 84, 86, 88, 78, 7.0, 6.5, None, "需数理/编程基础", "")),
    ("uk-warwick-mgmt", "英国", "华威大学", 67, "Management MSc", "管理学/商科",
     req(81, 83, 85, 87, 77, 7.0, 6.0, None, "非商科可申", "")),
    ("uk-man-fin", "英国", "曼彻斯特大学", 34, "Finance MSc", "金融",
     req(82, 85, 86, 88, 78, 7.0, 6.0, None, "需相关量化背景", "AMBS list，认院校")),
    ("uk-man-accfin", "英国", "曼彻斯特大学", 34, "Accounting and Finance MSc", "会计",
     req(81, 84, 85, 87, 77, 7.0, 6.0, None, "需会计/金融背景", "")),
    ("uk-man-finecon", "英国", "曼彻斯特大学", 34, "Financial Economics MSc", "金融",
     req(82, 84, 86, 88, 78, 7.0, 6.0, None, "需经济 + 数学背景", "金融经济，偏量化")),
    ("uk-man-econ", "英国", "曼彻斯特大学", 34, "Economics MSc", "经济学",
     req(81, 84, 85, 87, 77, 6.5, 6.0, None, "需经济本科 + 数学", "")),
    ("uk-ed-fin", "英国", "爱丁堡大学", 27, "Finance MSc", "金融",
     req(81, 84, 85, 87, 77, 7.0, 6.0, None, "需量化背景", "爱丁堡商学院 list 明确")),
    ("uk-ed-finmgmt", "英国", "爱丁堡大学", 27, "Financial Management MSc", "金融",
     req(80, 83, 85, 87, 76, 7.0, 6.0, None, "商科背景", "")),
    ("uk-ed-econ", "英国", "爱丁堡大学", 27, "Economics MSc", "经济学",
     req(81, 84, 85, 87, 77, 7.0, 6.0, None, "需经济 + 数学背景", "")),
    ("uk-ed-ba", "英国", "爱丁堡大学", 27, "Business Analytics MSc", "商业分析",
     req(81, 83, 85, 87, 77, 6.5, 6.0, None, "需数理基础", "")),
    ("uk-kcl-econ", "英国", "伦敦国王学院 KCL", 40, "Economics MSc", "经济学",
     req(81, 84, 85, 87, 77, 7.0, 6.5, None, "需经济 + 数学背景", "")),
    ("uk-kcl-bankfin", "英国", "伦敦国王学院 KCL", 40, "Banking & Finance MSc", "金融",
     req(81, 84, 85, 87, 77, 7.0, 6.5, None, "需量化/金融背景", "")),
    ("uk-kcl-accfin", "英国", "伦敦国王学院 KCL", 40, "Accounting, Accountability & Financial Management MSc", "会计",
     req(80, 83, 85, 87, 76, 7.0, 6.5, None, "会计/商科背景", "")),
    ("uk-kcl-ds", "英国", "伦敦国王学院 KCL", 40, "Data Science MSc", "数据科学/AI",
     req(81, 84, 85, 87, 77, 6.5, 6.0, None, "需编程/数理背景", "")),
    ("uk-bristol-econ", "英国", "布里斯托大学", 54, "Economics MSc", "经济学",
     req(80, 83, 85, 87, 76, 6.5, 6.5, None, "需经济 + 数学背景", "")),
    ("uk-bristol-fin", "英国", "布里斯托大学", 54, "Finance & Investment MSc", "金融",
     req(80, 83, 85, 87, 76, 6.5, 6.5, None, "需量化背景", "")),
    ("uk-bristol-accfin", "英国", "布里斯托大学", 54, "Accounting & Finance MSc", "会计",
     req(80, 83, 85, 87, 76, 6.5, 6.5, None, "会计/金融背景", "")),
    ("uk-glasgow-fin", "英国", "格拉斯哥大学", 76, "International Finance MSc", "金融",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需金融/商科背景", "亚当斯密商学院")),
    ("uk-glasgow-finecon", "英国", "格拉斯哥大学", 76, "Economics, Banking & Finance MSc", "金融",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需经济/数理背景", "经济+银行+金融交叉")),
    ("uk-glasgow-ba", "英国", "格拉斯哥大学", 76, "Business Analytics MSc", "商业分析",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需数理基础", "")),
    ("uk-durham-fin", "英国", "杜伦大学", 78, "Finance MSc", "金融",
     req(80, 83, 85, 87, 76, 7.0, 6.0, None, "需量化背景", "杜伦商学院 list 明确")),
    ("uk-durham-econ", "英国", "杜伦大学", 78, "Economics MSc", "经济学",
     req(80, 83, 85, 87, 76, 7.0, 6.0, None, "需经济 + 数学背景", "")),
    ("uk-durham-mgmt", "英国", "杜伦大学", 78, "Management MSc", "管理学/商科",
     req(79, 82, 84, 86, 75, 6.5, 6.0, None, "非商科可申", "")),
    ("uk-leeds-fin", "英国", "利兹大学", 82, "Finance MSc", "金融",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需量化背景", "")),
    ("uk-leeds-econ", "英国", "利兹大学", 82, "Economics MSc", "经济学",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需经济 + 数学背景", "")),
    ("uk-leeds-accfin", "英国", "利兹大学", 82, "Accounting & Finance MSc", "会计",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "会计/金融背景", "")),

    # ===================== 中国香港 =====================
    ("hk-hku-econ", "中国香港", "香港大学 HKU", 17, "Economics MEcon", "经济学",
     req(82, 85, 87, 88, 78, 7.0, 6.0, None, "需经济 + 数学背景", "港大经济，量化要求高")),
    ("hk-hku-fin", "中国香港", "香港大学 HKU", 17, "Finance MSc (MFin)", "金融",
     req(83, 85, 87, 88, 78, 7.0, 6.0, None, "需金融/量化背景", "港大金融热门，GMAT 加分")),
    ("hk-hku-acc", "中国香港", "香港大学 HKU", 17, "Accounting MSc", "会计",
     req(81, 84, 86, 88, 77, 7.0, 6.0, None, "会计/商科背景", "")),
    ("hk-cuhk-econ", "中国香港", "香港中文大学 CUHK", 36, "Economics MSc", "经济学",
     req(81, 84, 86, 88, 77, 6.5, 6.0, None, "需经济 + 数学背景", "")),
    ("hk-cuhk-acc", "中国香港", "香港中文大学 CUHK", 36, "Professional Accountancy MSc", "会计",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "会计/商科背景", "")),
    ("hk-cuhk-fintech", "中国香港", "香港中文大学 CUHK", 36, "Financial Technology MSc", "金融工程",
     req(81, 84, 86, 88, 77, 6.5, 6.0, None, "需编程/数理背景", "")),
    ("hk-hkust-fintech", "中国香港", "香港科技大学 HKUST", 47, "Financial Technology MSc", "金融工程",
     req(82, 85, 87, 88, 78, 6.5, 6.0, None, "需编程/数理/金融背景", "")),
    ("hk-hkust-im", "中国香港", "香港科技大学 HKUST", 47, "Investment Management MSc", "金融",
     req(82, 85, 87, 88, 78, 6.5, 6.0, None, "需金融/量化背景", "")),
    ("hk-hkust-econ", "中国香港", "香港科技大学 HKUST", 47, "Economics MSc", "经济学",
     req(81, 84, 86, 88, 77, 6.5, 6.0, None, "需经济 + 数学背景", "")),
    ("hk-hkust-bigdata", "中国香港", "香港科技大学 HKUST", 47, "Big Data Technology MSc", "数据科学/AI",
     req(82, 85, 87, 88, 78, 6.5, 6.0, None, "需编程/数理背景", "")),
    ("hk-cityu-fe", "中国香港", "香港城市大学 CityU", 62, "Financial Engineering MSc", "金融工程",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需强数理与编程背景", "")),
    ("hk-cityu-ba", "中国香港", "香港城市大学 CityU", 62, "Business Information Systems / Analytics MSc", "商业分析",
     req(77, 80, 82, 85, 73, 6.5, 6.0, None, "需数理基础", "")),
    ("hk-polyu-fin", "中国香港", "香港理工大学", 57, "Finance MSc (Investment Management)", "金融",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需金融/量化背景", "")),
    ("hk-polyu-acc", "中国香港", "香港理工大学", 57, "Professional Accounting MSc", "会计",
     req(77, 80, 82, 85, 73, 6.5, 6.0, None, "会计/商科背景", "")),

    # ===================== 新加坡 =====================
    ("sg-nus-fin", "新加坡", "新加坡国立大学 NUS", 8, "Finance MSc", "金融",
     req(83, 85, 87, 88, 78, 7.0, 6.5, None, "需金融/量化背景", "NUS 金融，认可院校 + GMAT 加分")),
    ("sg-nus-fe", "新加坡", "新加坡国立大学 NUS", 8, "Financial Engineering MSc", "金融工程",
     req(83, 85, 87, 88, 78, 6.5, 6.0, None, "需强数理与编程背景", "RMI 金融工程，偏量化")),
    ("sg-nus-econ", "新加坡", "新加坡国立大学 NUS", 8, "Economics MSc", "经济学",
     req(82, 85, 87, 88, 78, 6.5, 6.0, None, "需经济 + 数学背景", "")),
    ("sg-ntu-fin", "新加坡", "南洋理工大学 NTU", 15, "Finance MSc", "金融",
     req(82, 85, 87, 88, 78, 6.5, 6.0, None, "需金融/量化背景", "NBS 金融")),
    ("sg-ntu-fe", "新加坡", "南洋理工大学 NTU", 15, "Financial Engineering MSc", "金融工程",
     req(82, 85, 87, 88, 78, 6.5, 6.0, None, "需强数理与编程背景", "")),
    ("sg-smu-fin", "新加坡", "新加坡管理大学 SMU", 545, "Quantitative Finance MSc", "金融工程",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需数理/金融背景", "")),

    # ===================== 澳大利亚 =====================
    ("au-unimelb-fin", "澳大利亚", "墨尔本大学", 13, "Master of Finance", "金融",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需金融/量化背景", "墨尔本商学院，认 985/211 加权")),
    ("au-unimelb-econ", "澳大利亚", "墨尔本大学", 13, "Master of Economics", "经济学",
     req(79, 82, 84, 86, 75, 6.5, 6.0, None, "需经济 + 数学背景", "")),
    ("au-usyd-fin", "澳大利亚", "悉尼大学", 18, "Master of Commerce (Finance)", "金融",
     req(78, 81, 83, 85, 74, 7.0, 6.0, None, "商科背景", "")),
    ("au-unsw-fin", "澳大利亚", "新南威尔士大学 UNSW", 19, "Master of Finance", "金融",
     req(78, 81, 83, 85, 74, 7.0, 6.0, None, "需金融/量化背景", "")),
    ("au-monash-banking", "澳大利亚", "莫纳什大学", 37, "Master of Banking & Finance", "金融",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "需金融/商科背景", "")),

    # ===================== 美国（金融/金工高需求）=====================
    ("us-columbia-mfe", "美国", "哥伦比亚大学", 34, "Financial Engineering MS (MFE)", "金融工程",
     req(85, 87, 88, 90, 80, 7.0, 6.5, {"total": 325, "quant": 168}, "需强数理 + 编程（C++/Python）背景", "MFE 顶级项目，几乎必须 GRE 高分")),
    ("us-nyu-mscfin", "美国", "纽约大学 NYU", 38, "Mathematics in Finance MS", "金融工程",
     req(85, 87, 88, 90, 80, 7.0, 6.5, {"total": 325, "quant": 168}, "需数学/统计/工程背景", "Courant 数学金融，量化极强")),
    ("us-jhu-fin", "美国", "约翰霍普金斯大学 JHU", 28, "Financial Mathematics MS", "金融工程",
     req(83, 85, 87, 88, 78, 7.0, 6.5, {"total": 320, "quant": 165}, "需数理 + 编程背景", "")),
    ("us-usc-fin", "美国", "南加州大学 USC", 121, "Finance MS", "金融",
     req(82, 84, 86, 88, 78, 7.0, 6.5, {"total": 315, "quant": 162}, "需金融/量化背景", "")),
]


def build(country, qs, uni, program, field, requirements):
    return {
        "country": country,
        "university": uni,
        "qsRank": qs,
        "program": program,
        "field": field,
        "degree": "硕士",
        "requirements": requirements,
        "tuition": TUI.get(country, "学费见官网"),
        "duration": DUR.get(country, ""),
        "timeline": TL.get(country, "申请时间见官网"),
    }


added = 0
skipped = 0
for pid, country, uni, qs, program, field, requirements in NEW:
    if pid in existing_ids or (uni, program) in existing_pairs:
        skipped += 1
        continue
    entry = {"id": pid}
    entry.update(build(country, qs, uni, program, field, requirements))
    programs.append(entry)
    existing_ids.add(pid)
    existing_pairs.add((uni, program))
    added += 1

data["meta"]["updated"] = "2026-06"
data["meta"]["count"] = len(programs)

json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"新增 {added} 个，跳过 {skipped} 个（已存在），现共 {len(programs)} 个项目")
