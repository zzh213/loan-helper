#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第六批扩充：加拿大深化 + 新增爱尔兰（都柏林圣三一/UCD）+ 港澳新深化
+ 补强薄弱方向（材料/环境/翻译/设计/公共政策/心理/通信/信息系统）。
真实项目名 + 公开经验参考线（非官方保证）。按 id/(校,项目) 去重，可重复运行。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "programs.json")
data = json.load(open(PATH, encoding="utf-8"))
programs = data["programs"]
ids = {p["id"] for p in programs}
pairs = {(p["university"], p["program"]) for p in programs}


def req(a985, a211, asy, asf, ahb, io=6.5, isub=6.0, gre=None, bg="", notes=""):
    return {"avgByTier": {"985": a985, "211": a211, "双一流": asy, "双非": asf, "海本/中外合作": ahb},
            "ielts": {"overall": io, "sub": isub}, "gre": gre, "background": bg, "notes": notes}


TUI = {"英国": "约 25–38 万元 / 1年", "中国香港": "约 14–28 万元 / 1年",
       "新加坡": "约 18–32 万元 / 1–1.5年", "澳大利亚": "约 20–35 万元 / 1.5–2年",
       "美国": "约 35–60 万元 / 1–2年", "加拿大": "约 18–35 万元 / 1–2年",
       "爱尔兰": "约 16–28 万元 / 1年"}
DUR = {"英国": "1 年", "中国香港": "1 年", "新加坡": "1–1.5 年", "澳大利亚": "1.5–2 年",
       "美国": "1–2 年", "加拿大": "1–2 年", "爱尔兰": "1 年"}
TL = {"英国": "每年 9–10 月开放，滚动录取先到先得，建议 10–12 月递交",
      "中国香港": "每年 9 月开放，多轮截止，建议首轮（10–12 月）递交",
      "新加坡": "每年 10–11 月开放，建议次年 1–2 月前递交",
      "澳大利亚": "多为两次入学（2 月 / 7 月），常年滚动审理",
      "美国": "每年 9 月开放，截止 12 月–次年 1 月，部分有早申轮次",
      "加拿大": "每年 9–10 月开放，截止次年 1–3 月，名额有限建议早申",
      "爱尔兰": "每年 10 月开放，滚动录取，建议次年 1–3 月前递交"}

NEW = [
    # ===================== 加拿大深化 =====================
    ("ca-toronto-cs", "加拿大", "多伦多大学", 25, "Master of Science in Applied Computing (MScAC)", "计算机/CS",
     req(85, 87, 88, 90, 80, 7.0, 6.5, "GRE 建议，量化", "需 CS/相关强背景 + 编程", "多大 MScAC 含 8 个月产业实习，竞争激烈")),
    ("ca-toronto-ms", "加拿大", "多伦多大学", 25, "Master of Management Analytics (MMA)", "商业分析",
     req(84, 86, 87, 88, 79, 7.0, 6.5, "GMAT/GRE 建议", "需数理/编程基础", "Rotman 商学院，就业导向")),
    ("ca-toronto-eng", "加拿大", "多伦多大学", 25, "Master of Engineering (MEng) ECE", "电子/电气工程",
     req(83, 85, 86, 88, 78, 6.5, 6.0, None, "需工程/相关本科背景", "可授课或含实习方向")),
    ("ca-ubc-ds", "加拿大", "英属哥伦比亚大学 UBC", 38, "Master of Data Science (MDS)", "数据科学/AI",
     req(84, 86, 87, 89, 80, 6.5, 6.0, "GRE 可选", "需数理 + 编程背景", "10 个月密集项目，需先修课")),
    ("ca-ubc-ba", "加拿大", "英属哥伦比亚大学 UBC", 38, "Master of Business Analytics (MBAN)", "商业分析",
     req(83, 85, 86, 88, 79, 6.5, 6.0, "GMAT/GRE 建议", "需量化背景", "Sauder 商学院")),
    ("ca-mcgill-fin", "加拿大", "麦吉尔大学", 29, "Master of Management in Finance (MMF)", "金融",
     req(83, 85, 86, 88, 79, 6.5, 6.0, "GMAT/GRE 建议", "需商科/量化背景", "Desautels 管理学院")),
    ("ca-mcgill-analytics", "加拿大", "麦吉尔大学", 29, "Master of Management in Analytics (MMA)", "商业分析",
     req(83, 85, 86, 88, 79, 6.5, 6.0, "GMAT/GRE 建议", "需数理/编程基础", "")),
    ("ca-waterloo-cs", "加拿大", "滑铁卢大学", 112, "Master of Data Science and Artificial Intelligence", "数据科学/AI",
     req(84, 86, 87, 89, 80, 6.5, 6.5, "GRE 可选", "需 CS/数理背景 + 编程", "滑铁卢工科强，实习文化浓")),
    ("ca-alberta-cs", "加拿大", "阿尔伯塔大学", 96, "Master of Science in Computing Science", "计算机/CS",
     req(82, 84, 85, 87, 78, 6.5, 6.0, "GRE 可选", "需 CS 背景", "AI/强化学习方向知名")),
    ("ca-mcmaster-eng", "加拿大", "麦克马斯特大学", 176, "Master of Engineering in Systems and Technology", "电子/电气工程",
     req(80, 82, 84, 86, 76, 6.5, 6.0, None, "需工程本科背景", "")),
    ("ca-queens-analytics", "加拿大", "女王大学", 209, "Master of Management Analytics (MMA)", "商业分析",
     req(80, 82, 84, 86, 76, 7.0, 6.5, "GMAT/GRE 建议", "需量化基础", "Smith 商学院")),
    ("ca-western-fin", "加拿大", "西安大略大学", 114, "MSc in Management (Finance)", "金融",
     req(80, 82, 84, 86, 76, 6.5, 6.0, "GMAT/GRE 建议", "需商科背景", "Ivey/DAN 管理")),

    # ===================== 爱尔兰（新增地区）=====================
    ("ie-tcd-cs", "爱尔兰", "都柏林圣三一大学 TCD", 75, "MSc in Computer Science (Intelligent Systems)", "计算机/CS",
     req(80, 82, 84, 86, 76, 6.5, 6.0, None, "需 CS/相关背景 + 编程", "爱尔兰第一学府，2:1 荣誉学位")),
    ("ie-tcd-fin", "爱尔兰", "都柏林圣三一大学 TCD", 75, "MSc in Finance", "金融",
     req(82, 84, 85, 87, 78, 6.5, 6.0, "GMAT/GRE 建议", "需商科/量化背景", "Trinity Business School")),
    ("ie-tcd-ba", "爱尔兰", "都柏林圣三一大学 TCD", 75, "MSc in Business Analytics", "商业分析",
     req(81, 83, 85, 86, 77, 6.5, 6.0, None, "需数理/编程基础", "")),
    ("ie-ucd-cs", "爱尔兰", "都柏林大学 UCD", 126, "MSc in Computer Science (Negotiated Learning)", "计算机/CS",
     req(78, 80, 82, 84, 74, 6.5, 6.0, None, "需 CS 相关背景", "UCD Smurfit 商学院享誉")),
    ("ie-ucd-fin", "爱尔兰", "都柏林大学 UCD", 126, "MSc in Finance", "金融",
     req(80, 82, 84, 86, 76, 6.5, 6.0, "GMAT/GRE 建议", "需商科/量化背景", "Smurfit 商学院，三重认证")),
    ("ie-ucd-quant", "爱尔兰", "都柏林大学 UCD", 126, "MSc in Quantitative Finance", "金融工程",
     req(82, 84, 85, 87, 78, 6.5, 6.0, "GRE 量化建议", "需强数理 + 编程", "")),

    # ===================== 香港深化 =====================
    ("hk-ust-ba", "中国香港", "香港科技大学 HKUST", 44, "MSc in Business Analytics", "商业分析",
     req(85, 87, 88, 89, 80, 6.5, 5.5, "GMAT/GRE 建议", "需数理/编程基础", "科大商学院热门项目，竞争激烈")),
    ("hk-ust-fintech", "中国香港", "香港科技大学 HKUST", 44, "MSc in Financial Technology (FinTech)", "金融工程",
     req(85, 87, 88, 89, 80, 6.5, 5.5, "GRE 建议", "需金融/CS/数理跨学科背景", "工/商/理三院联合")),
    ("hk-ust-it", "中国香港", "香港科技大学 HKUST", 44, "MSc in Information Technology", "信息系统/IT",
     req(82, 84, 85, 87, 78, 6.0, 5.5, None, "需理工/计算背景", "")),
    ("hk-cuhk-fintech", "中国香港", "香港中文大学 CUHK", 36, "MSc in FinTech", "金融工程",
     req(84, 86, 87, 88, 79, 6.5, 6.0, None, "需金融/CS/工程背景", "中大工程学院与商学院合办")),
    ("hk-cuhk-ise", "中国香港", "香港中文大学 CUHK", 36, "MSc in Information Engineering", "通信工程",
     req(82, 84, 85, 87, 78, 6.5, 6.0, None, "需 EE/通信/CS 背景", "")),
    ("hk-cuhk-translation", "中国香港", "香港中文大学 CUHK", 36, "MA in Translation", "翻译/语言",
     req(82, 84, 85, 87, 78, 6.5, 6.0, None, "需语言/翻译相关背景，或通过笔试", "中大翻译学系久负盛名")),
    ("hk-cityu-ee", "中国香港", "香港城市大学 CityU", 62, "MSc in Electronic Information Engineering", "电子/电气工程",
     req(80, 82, 83, 85, 76, 6.5, 6.0, None, "需 EE/电子相关背景", "")),
    ("hk-cityu-data", "中国香港", "香港城市大学 CityU", 62, "MSc in Data Science", "数据科学/AI",
     req(82, 84, 85, 87, 78, 6.5, 6.0, None, "需数理/编程背景", "")),
    ("hk-polyu-aviation", "中国香港", "香港理工大学 PolyU", 57, "MSc in Data Science and Analytics", "数据科学/AI",
     req(81, 83, 84, 86, 77, 6.5, 6.0, None, "需数理/编程基础", "理大应用数学系")),
    ("hk-polyu-design", "中国香港", "香港理工大学 PolyU", 57, "Master of Design (Design Strategies)", "设计/艺术",
     req(78, 80, 82, 84, 74, 6.5, 6.0, None, "需设计相关背景 + 作品集", "理大设计学院亚洲顶尖")),

    # ===================== 新加坡深化 =====================
    ("sg-smu-fin", "新加坡", "新加坡管理大学 SMU", 545, "Master of Science in Finance (Quantitative Finance)", "金融工程",
     req(84, 86, 87, 88, 79, 7.0, 6.5, "GMAT/GRE 建议", "需强数理 + 编程", "SMU 李光前商学院")),
    ("sg-smu-analytics", "新加坡", "新加坡管理大学 SMU", 545, "Master of IT in Business (Analytics)", "商业分析",
     req(83, 85, 86, 87, 78, 7.0, 6.5, None, "需数理/编程基础", "")),
    ("sg-nus-eco", "新加坡", "新加坡国立大学 NUS", 8, "Master of Economics", "经济学",
     req(87, 89, 90, 91, 82, 7.0, 6.5, "GRE 建议", "需经济/数理背景", "NUS 经济系排名亚洲前列")),
    ("sg-ntu-comm", "新加坡", "南洋理工大学 NTU", 15, "MSc in Communication Studies", "传媒",
     req(83, 85, 86, 88, 79, 7.0, 6.5, None, "需传播/社科相关背景", "黄金辉传播与信息学院")),
    ("sg-ntu-supply", "新加坡", "南洋理工大学 NTU", 15, "MSc in Supply Chain Engineering", "机械工程",
     req(82, 84, 85, 87, 78, 6.5, 6.0, None, "需工程/理科背景", "")),

    # ===================== 英国补强薄弱方向 =====================
    ("uk-ucl-env", "英国", "伦敦大学学院 UCL", 9, "Environmental Systems Engineering MSc", "环境科学",
     req(83, 85, 86, 88, 78, 6.5, 6.0, None, "需工程/环境/理科背景", "UCL 2:1 荣誉学位")),
    ("uk-imperial-materials", "英国", "帝国理工学院 IC", 2, "Advanced Materials Science and Engineering MSc", "材料工程",
     req(85, 87, 88, 89, 80, 6.5, 6.0, None, "需材料/化学/物理/工程背景", "IC 材料系全球顶尖，2:1 学位")),
    ("uk-manchester-materials", "英国", "曼彻斯特大学", 34, "Advanced Materials MSc", "材料工程",
     req(80, 82, 84, 86, 76, 6.5, 6.0, None, "需材料/化学/工程背景", "")),
    ("uk-leeds-comm", "英国", "利兹大学", 82, "Communication and Media MA", "传媒",
     req(80, 82, 83, 85, 76, 6.5, 6.0, None, "需传媒/社科相关背景", "利兹传媒学院口碑好")),
    ("uk-warwick-psych", "英国", "华威大学", 69, "Behavioural and Data Science MSc", "心理学",
     req(83, 85, 86, 88, 78, 7.0, 6.5, None, "需心理/社科/数理背景", "华威心理系交叉方向")),
    ("uk-bristol-env", "英国", "布里斯托大学", 54, "Environmental Policy and Management MSc", "环境科学",
     req(80, 82, 84, 86, 76, 6.5, 6.0, None, "需相关社科/理科背景", "")),
    ("uk-edinburgh-translation", "英国", "爱丁堡大学", 27, "Translation Studies MSc", "翻译/语言",
     req(82, 84, 85, 87, 78, 7.0, 6.5, None, "需语言/翻译相关背景", "爱大 2:1 学位，语言测试")),
    ("uk-durham-pp", "英国", "杜伦大学", 89, "Public Policy MPP", "公共政策/管理",
     req(82, 84, 85, 87, 78, 6.5, 6.0, None, "需社科/政治/经济背景", "杜伦政府学院")),
    ("uk-glasgow-design", "英国", "格拉斯哥大学", 76, "Information Technology: Software & Systems MSc", "信息系统/IT",
     req(80, 82, 84, 85, 76, 6.5, 6.0, None, "适合非计算背景转 IT", "格大 IT 转专业友好")),

    # ===================== 美国补强 =====================
    ("us-cmu-si", "美国", "卡内基梅隆大学 CMU", 52, "Master of Information Systems Management (MISM)", "信息系统/IT",
     req(86, 88, 89, 90, 82, 7.0, 6.5, "GRE 建议", "需一定编程/数理基础", "CMU Heinz 学院，就业强")),
    ("us-nyu-comm", "美国", "纽约大学 NYU", 39, "MA in Media, Culture, and Communication", "传媒",
     req(84, 86, 87, 88, 80, 7.0, 6.5, "GRE 可选", "需传播/社科相关背景", "NYU Steinhardt")),
    ("us-umich-env", "美国", "密歇根大学安娜堡分校", 44, "Master of Science in Environment and Sustainability", "环境科学",
     req(83, 85, 86, 88, 79, 7.0, 6.5, "GRE 可选", "需环境/理科背景", "")),
    ("us-gatech-ece", "美国", "佐治亚理工学院", 82, "MS in Electrical and Computer Engineering", "电子/电气工程",
     req(85, 87, 88, 89, 81, 7.0, 6.5, "GRE 强烈建议", "需 EE/ECE 强背景", "GT 工科顶尖")),
    ("us-usc-cs", "美国", "南加州大学 USC", 121, "MS in Computer Science", "计算机/CS",
     req(84, 86, 87, 88, 80, 7.0, 6.5, "GRE 建议", "需 CS 背景 + 编程", "USC Viterbi 中国学生多")),

    # ===================== 澳大利亚补强 =====================
    ("au-unimelb-it", "澳大利亚", "墨尔本大学", 13, "Master of Information Technology", "信息系统/IT",
     req(80, 82, 84, 86, 76, 6.5, 6.0, None, "可接受非计算背景（部分方向）", "墨大 IT，转专业友好")),
    ("au-unsw-fin", "澳大利亚", "新南威尔士大学 UNSW", 19, "Master of Financial Analysis", "金融",
     req(80, 82, 84, 86, 76, 7.0, 6.0, None, "需商科/会计/金融背景", "UNSW 商学院")),
    ("au-sydney-ba", "澳大利亚", "悉尼大学", 18, "Master of Data Science", "数据科学/AI",
     req(80, 82, 84, 86, 76, 6.5, 6.0, None, "需数理/编程背景", "")),
    ("au-monash-eng", "澳大利亚", "莫纳什大学", 37, "Master of Advanced Engineering (Materials)", "材料工程",
     req(78, 80, 82, 84, 74, 6.5, 6.0, None, "需工程/材料本科背景", "")),
]


def build(country, uni, qs, program, field, requirements):
    return {"country": country, "university": uni, "qsRank": qs, "program": program,
            "field": field, "degree": "硕士", "requirements": requirements,
            "tuition": TUI.get(country, "学费见官网"), "duration": DUR.get(country, ""),
            "timeline": TL.get(country, "申请时间见官网")}


added = skipped = 0
for pid, country, uni, qs, program, field, requirements in NEW:
    if pid in ids or (uni, program) in pairs:
        skipped += 1
        continue
    entry = {"id": pid}
    entry.update(build(country, uni, qs, program, field, requirements))
    q = f"{uni} {program} entry requirements"
    entry["provenance"] = {
        "dataSource": "参考估算", "verified": False, "lastVerified": None,
        "sourceUrl": None,
        "searchUrl": "https://www.google.com/search?q=" + q.replace(" ", "+"),
    }
    programs.append(entry)
    ids.add(pid)
    pairs.add((uni, program))
    added += 1

data["meta"]["count"] = len(programs)
data["meta"]["verifiedCount"] = sum(1 for p in programs if p.get("provenance", {}).get("verified"))
# 同步 meta 里国家列表用到的字段/tier 不变；新增地区仅体现在数据中
json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"新增 {added} 个，跳过 {skipped} 个，现共 {len(programs)} 个项目")
