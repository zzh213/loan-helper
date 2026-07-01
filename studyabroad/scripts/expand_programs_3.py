#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三批扩充：新增加拿大（多伦多/UBC/麦吉尔/滑铁卢）+ 补英国热门校（诺丁汉/巴斯/约克/利物浦/纽卡/UEA/兰卡/埃克塞特）
+ 港澳补强（浸会/阿德莱德/西澳/UTS）。分数线为公开经验参考线，非官方保证。去重安全、可重复运行。
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


TUI = {"英国": "约 25–38 万元 / 1年", "中国香港": "约 14–28 万元 / 1年", "新加坡": "约 18–32 万元 / 1–1.5年",
       "澳大利亚": "约 20–35 万元 / 1.5–2年", "美国": "约 35–60 万元 / 1–2年", "加拿大": "约 18–35 万元 / 1–2年"}
DUR = {"英国": "1 年", "中国香港": "1 年", "新加坡": "1–1.5 年", "澳大利亚": "1.5–2 年",
       "美国": "1–2 年", "加拿大": "1–2 年"}
TL = {"英国": "每年 9–10 月开放，滚动录取先到先得，建议 10–12 月递交",
      "中国香港": "每年 9 月开放，多轮截止，建议首轮（10–12 月）递交",
      "新加坡": "每年 10–11 月开放，建议次年 1–2 月前递交",
      "澳大利亚": "多为两次入学（2 月 / 7 月），常年滚动审理",
      "美国": "每年 9 月开放，截止 12 月–次年 1 月，部分有早申轮次",
      "加拿大": "每年 9–10 月开放，截止 12 月–次年 2 月，名额有限建议早申"}

NEW = [
    # ===================== 加拿大（全新国家）=====================
    ("ca-toronto-cs", "加拿大", "多伦多大学", 25, "Master of Science in Applied Computing (MScAC)", "计算机/CS",
     req(85, 87, 88, 90, 80, 7.0, 6.5, None, "需 CS 背景 + 科研/项目", "多大 MScAC 含产业实习，竞争激烈")),
    ("ca-toronto-ds", "加拿大", "多伦多大学", 25, "Master of Data Science & Machine Learning", "数据科学/AI",
     req(84, 86, 88, 89, 79, 7.0, 6.5, None, "需数理 + 编程背景", "")),
    ("ca-toronto-fin", "加拿大", "多伦多大学", 25, "Master of Financial Economics", "金融",
     req(84, 86, 88, 89, 79, 7.0, 6.5, None, "需经济/金融 + 数学背景", "罗特曼商学院，量化要求高")),
    ("ca-ubc-cs", "加拿大", "英属哥伦比亚大学 UBC", 38, "Master of Data Science", "数据科学/AI",
     req(83, 85, 87, 88, 78, 6.5, 6.0, None, "需数理 + 编程背景", "UBC MDS 一年制就业导向")),
    ("ca-ubc-fin", "加拿大", "英属哥伦比亚大学 UBC", 38, "Master of Management / Finance", "金融",
     req(82, 84, 86, 88, 78, 7.0, 6.5, None, "商科/量化背景", "")),
    ("ca-mcgill-cs", "加拿大", "麦吉尔大学", 27, "Master of Science (Computer Science)", "计算机/CS",
     req(83, 85, 87, 88, 78, 6.5, 6.0, None, "需 CS 背景", "")),
    ("ca-mcgill-fin", "加拿大", "麦吉尔大学", 27, "Master of Management in Finance", "金融",
     req(82, 84, 86, 88, 78, 6.5, 6.0, None, "商科/量化背景", "Desautels 商学院")),
    ("ca-waterloo-cs", "加拿大", "滑铁卢大学", 112, "Master of Data Science & Artificial Intelligence", "数据科学/AI",
     req(82, 84, 86, 88, 78, 6.5, 6.5, None, "需 CS/数理背景", "滑铁卢 CS/AI 北美强校，重 co-op")),
    ("ca-waterloo-eng", "加拿大", "滑铁卢大学", 112, "Master of Engineering (ECE)", "电子/电气工程",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需 EE/工科背景", "")),

    # ===================== 英国补强热门校 =====================
    ("uk-nottingham-cs", "英国", "诺丁汉大学", 97, "Computer Science MSc", "计算机/CS",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需相关背景", "")),
    ("uk-nottingham-fin", "英国", "诺丁汉大学", 97, "Finance & Investment MSc", "金融",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需金融/量化背景", "")),
    ("uk-bath-fin", "英国", "巴斯大学", 150, "Finance MSc", "金融",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需量化背景", "巴斯管理学院金融强")),
    ("uk-bath-ba", "英国", "巴斯大学", 150, "Business Analytics MSc", "商业分析",
     req(79, 82, 84, 86, 75, 6.5, 6.0, None, "需数理基础", "")),
    ("uk-bath-mgmt", "英国", "巴斯大学", 150, "Management MSc", "管理学/商科",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "商科/社科背景", "")),
    ("uk-york-cs", "英国", "约克大学", 162, "Computer Science MSc", "计算机/CS",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "转专业友好", "可接受非 CS 背景")),
    ("uk-york-ds", "英国", "约克大学", 162, "Data Science MSc", "数据科学/AI",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "需数理基础", "")),
    ("uk-liverpool-cs", "英国", "利物浦大学", 165, "Computer Science MSc", "计算机/CS",
     req(75, 78, 80, 83, 71, 6.5, 6.0, None, "需相关背景", "")),
    ("uk-liverpool-fin", "英国", "利物浦大学", 165, "Finance MSc", "金融",
     req(75, 78, 80, 83, 71, 6.5, 6.0, None, "需金融/商科背景", "")),
    ("uk-newcastle-fin", "英国", "纽卡斯尔大学", 129, "Finance MSc", "金融",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "需金融/商科背景", "")),
    ("uk-newcastle-ba", "英国", "纽卡斯尔大学", 129, "Business Analytics MSc", "商业分析",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "需数理基础", "")),
    ("uk-uea-fin", "英国", "东英吉利大学 UEA", 304, "Finance & Management MSc", "金融",
     req(73, 76, 79, 82, 69, 6.5, 6.0, None, "商科背景", "")),
    ("uk-lancaster-fin", "英国", "兰卡斯特大学", 132, "Finance MSc", "金融",
     req(78, 81, 83, 85, 74, 7.0, 6.0, None, "需量化背景", "兰卡管理学院 list 明确")),
    ("uk-exeter-fin", "英国", "埃克塞特大学", 153, "Finance & Investment MSc", "金融",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需金融/量化背景", "")),
    ("uk-sheffield-cs", "英国", "谢菲尔德大学", 105, "Computer Science (Conversion) MSc", "计算机/CS",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "转专业友好", "")),

    # ===================== 港澳补强 =====================
    ("hk-hkbu-comm", "中国香港", "香港浸会大学 HKBU", 252, "Communication MA", "传媒",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "传媒/文科背景", "浸会传理学院亚洲知名")),
    ("hk-hkbu-ai", "中国香港", "香港浸会大学 HKBU", 252, "Artificial Intelligence MSc", "数据科学/AI",
     req(75, 78, 80, 83, 71, 6.5, 6.0, None, "需 CS/数理背景", "")),
    ("hk-polyu-ds", "中国香港", "香港理工大学", 57, "Data Science & Analytics MSc", "数据科学/AI",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需数理 + 编程基础", "")),
    ("au-adelaide-ds", "澳大利亚", "阿德莱德大学", 82, "Master of Data Science", "数据科学/AI",
     req(74, 77, 79, 82, 70, 6.5, 6.0, None, "需数理基础", "")),
    ("au-uwa-fin", "澳大利亚", "西澳大学 UWA", 77, "Master of Finance", "金融",
     req(74, 77, 79, 82, 70, 6.5, 6.0, None, "商科/量化背景", "")),
    ("au-uts-ds", "澳大利亚", "悉尼科技大学 UTS", 88, "Master of Data Science & Innovation", "数据科学/AI",
     req(73, 76, 78, 81, 69, 6.5, 6.0, None, "需数理基础", "")),
]


def build(country, qs, uni, program, field, requirements):
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
    entry.update(build(country, qs, uni, program, field, requirements))
    # 加默认溯源（参考估算）
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
json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"新增 {added} 个，跳过 {skipped} 个，现共 {len(programs)} 个项目")
