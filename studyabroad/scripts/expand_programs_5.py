#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第五批扩充：补强美国顶尖名校（MIT/哈佛/普林斯顿/UChicago/UPenn/杜克/UCSD/UT Austin/UW/Purdue/NYU 等）
覆盖金融/金融工程/经济/统计/CS/DS·AI/商业分析/MEM。真实项目名 + 公开经验参考线（非官方保证）。去重安全、可重复运行。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "programs.json")
data = json.load(open(PATH, encoding="utf-8"))
programs = data["programs"]
ids = {p["id"] for p in programs}
pairs = {(p["university"], p["program"]) for p in programs}


def req(a985, a211, asy, asf, ahb, io=7.0, isub=6.5, gre=None, bg="", notes=""):
    return {"avgByTier": {"985": a985, "211": a211, "双一流": asy, "双非": asf, "海本/中外合作": ahb},
            "ielts": {"overall": io, "sub": isub}, "gre": gre, "background": bg, "notes": notes}


TUI = "约 35–70 万元 / 1–2年"
DUR = "1–2 年"
TL = "每年 9 月开放，截止 12 月–次年 1 月，部分项目有早申/滚动轮次"

NEW = [
    # ===================== MIT =====================
    ("us-mit-fin", "美国", "麻省理工学院 MIT", 1, "Master of Finance (MFin)", "金融",
     req(90, 92, 93, 94, 86, 7.0, 6.5, "GRE/GMAT 强烈建议，量化高分",
         "需量化背景 + 实习/科研", "MIT Sloan MFin 全球顶尖，竞争极激烈")),
    ("us-mit-bizanalytics", "美国", "麻省理工学院 MIT", 1, "Master of Business Analytics", "商业分析",
     req(90, 92, 93, 94, 86, 7.0, 6.5, "GRE/GMAT 建议", "需数理 + 编程背景", "MIT Sloan + ORC，重运筹与机器学习")),
    ("us-mit-eecs", "美国", "麻省理工学院 MIT", 1, "Master of Engineering in EECS", "计算机/CS",
     req(90, 92, 93, 94, 86, 7.0, 6.5, "GRE 视项目", "需 CS/EE 背景 + 强科研", "")),

    # ===================== 哈佛 / 普林斯顿 / 耶鲁 =====================
    ("us-harvard-ds", "美国", "哈佛大学", 4, "Master of Science in Data Science", "数据科学/AI",
     req(90, 92, 93, 94, 86, 7.0, 6.5, "GRE 建议", "需数理 + 编程背景 + 科研", "哈佛 SEAS + 统计系合办")),
    ("us-harvard-cse", "美国", "哈佛大学", 4, "Master in Computational Science & Engineering", "数据科学/AI",
     req(89, 91, 92, 93, 85, 7.0, 6.5, "GRE 建议", "需数理/工科背景", "")),
    ("us-princeton-fin", "美国", "普林斯顿大学", 6, "Master in Finance (MFin)", "金融工程",
     req(90, 92, 93, 94, 86, 7.0, 6.5, "GRE 量化高分必备", "需强数理 + 编程", "普林斯顿 Bendheim 金工，量化导向，难度极高")),
    ("us-yale-fin", "美国", "耶鲁大学", 16, "Master of Management Studies in Asset Management", "金融",
     req(89, 91, 92, 93, 85, 7.0, 6.5, "GRE/GMAT 建议", "需金融/量化背景", "耶鲁管理学院")),

    # ===================== UChicago =====================
    ("us-uchicago-fin", "美国", "芝加哥大学", 21, "Master of Science in Financial Mathematics", "金融工程",
     req(88, 90, 91, 92, 84, 7.0, 6.5, "GRE 量化高分", "需强数理 + 编程", "UChicago MSFM 金工名项目")),
    ("us-uchicago-ds", "美国", "芝加哥大学", 21, "Master of Science in Applied Data Science", "数据科学/AI",
     req(87, 89, 90, 91, 83, 7.0, 6.5, "GRE optional", "需数理 + 编程背景", "")),
    ("us-uchicago-stat", "美国", "芝加哥大学", 21, "Master of Science in Statistics", "数据科学/AI",
     req(87, 89, 90, 91, 83, 7.0, 6.5, "GRE 建议", "需强数理背景", "")),
    ("us-uchicago-econ", "美国", "芝加哥大学", 21, "MA in Computational Social Science / Economics", "经济学",
     req(88, 90, 91, 92, 84, 7.0, 6.5, "GRE 建议", "需经济/数理背景", "芝加哥经济学全球顶尖")),

    # ===================== UPenn =====================
    ("us-upenn-ds", "美国", "宾夕法尼亚大学 UPenn", 11, "Master of Science in Engineering in Data Science", "数据科学/AI",
     req(87, 89, 90, 91, 83, 7.0, 6.5, "GRE optional", "需数理 + 编程背景", "")),
    ("us-upenn-cis", "美国", "宾夕法尼亚大学 UPenn", 11, "Master of Science in Engineering in CIS", "计算机/CS",
     req(87, 89, 90, 91, 83, 7.0, 6.5, "GRE optional", "需 CS 背景", "")),
    ("us-upenn-mcit", "美国", "宾夕法尼亚大学 UPenn", 11, "Master of Computer & Information Technology (MCIT)", "计算机/CS",
     req(85, 87, 88, 90, 80, 7.0, 6.5, "GRE optional", "面向转码（非 CS 背景友好）", "MCIT 接受零基础转码")),

    # ===================== 杜克 / 西北 / JHU =====================
    ("us-duke-fin", "美国", "杜克大学", 50, "Master of Quantitative Management (MQM)", "商业分析",
     req(85, 87, 88, 90, 80, 7.0, 6.5, "GRE/GMAT 建议", "商科/量化背景", "杜克 Fuqua MQM")),
    ("us-duke-ece", "美国", "杜克大学", 50, "Master of Science in ECE", "电子/电气工程",
     req(84, 86, 88, 89, 80, 7.0, 6.5, "GRE 建议", "需 EE/工科背景", "")),
    ("us-northwestern-ms", "美国", "西北大学", 47, "Master of Science in Analytics (MSiA)", "商业分析",
     req(86, 88, 89, 90, 82, 7.0, 6.5, "GRE 建议", "需数理 + 编程背景", "西北 MSiA 数据科学强项目")),
    ("us-jhu-fin", "美国", "约翰霍普金斯大学 JHU", 28, "Master of Science in Finance", "金融",
     req(84, 86, 88, 89, 80, 7.0, 6.5, "GRE/GMAT 建议", "需金融/量化背景", "Carey 商学院")),

    # ===================== UCSD / UT Austin / UW / Purdue =====================
    ("us-ucsd-cs", "美国", "加州大学圣地亚哥分校 UCSD", 72, "Master of Science in Computer Science", "计算机/CS",
     req(85, 87, 88, 90, 80, 7.0, 6.5, "GRE 建议", "需 CS 背景", "")),
    ("us-ucsd-ds", "美国", "加州大学圣地亚哥分校 UCSD", 72, "Master of Data Science", "数据科学/AI",
     req(84, 86, 88, 89, 80, 7.0, 6.5, "GRE optional", "需数理 + 编程背景", "")),
    ("us-utaustin-cs", "美国", "德州大学奥斯汀分校 UT Austin", 58, "Master of Science in Computer Science", "计算机/CS",
     req(85, 87, 88, 90, 80, 7.0, 6.5, "GRE 建议", "需 CS 背景", "")),
    ("us-utaustin-ba", "美国", "德州大学奥斯汀分校 UT Austin", 58, "Master of Science in Business Analytics", "商业分析",
     req(84, 86, 88, 89, 80, 7.0, 6.5, "GRE/GMAT 建议", "商科/数理背景", "McCombs 商学院")),
    ("us-uw-cs", "美国", "华盛顿大学 UW", 63, "Master of Science in Computer Science & Engineering", "计算机/CS",
     req(85, 87, 88, 90, 80, 7.0, 6.5, "GRE 建议", "需 CS 背景 + 科研", "西雅图地利，就业好")),
    ("us-uw-ds", "美国", "华盛顿大学 UW", 63, "Master of Science in Data Science", "数据科学/AI",
     req(84, 86, 88, 89, 80, 7.0, 6.5, "GRE optional", "需数理 + 编程背景", "")),
    ("us-purdue-ece", "美国", "普渡大学", 99, "Master of Science in ECE", "电子/电气工程",
     req(82, 84, 86, 88, 78, 7.0, 6.5, "GRE 建议", "需 EE/工科背景", "普渡工科强校")),
    ("us-purdue-cs", "美国", "普渡大学", 99, "Master of Science in Computer Science", "计算机/CS",
     req(83, 85, 87, 88, 79, 7.0, 6.5, "GRE 建议", "需 CS 背景", "")),

    # ===================== 哥大/康奈尔补充金工与统计 =====================
    ("us-columbia-fe", "美国", "哥伦比亚大学", 34, "Master of Science in Financial Engineering", "金融工程",
     req(89, 91, 92, 93, 85, 7.0, 6.5, "GRE 量化高分必备", "需强数理 + 编程", "哥大 MSFE 金工顶尖项目")),
    ("us-cornell-orie", "美国", "康奈尔大学", 16, "Master of Engineering in ORIE (Financial Engineering)", "金融工程",
     req(88, 90, 91, 92, 84, 7.0, 6.5, "GRE 量化高分", "需强数理 + 编程", "康奈尔 ORIE 金工方向")),
    ("us-cornell-stat", "美国", "康奈尔大学", 16, "Master of Professional Studies in Applied Statistics", "数据科学/AI",
     req(85, 87, 88, 90, 80, 7.0, 6.5, "GRE 建议", "需数理背景", "")),
]


def build(uni, qs, program, field, requirements):
    return {"country": "美国", "university": uni, "qsRank": qs, "program": program,
            "field": field, "degree": "硕士", "requirements": requirements,
            "tuition": TUI, "duration": DUR, "timeline": TL}


added = skipped = 0
for pid, country, uni, qs, program, field, requirements in NEW:
    if pid in ids or (uni, program) in pairs:
        skipped += 1
        continue
    entry = {"id": pid}
    entry.update(build(uni, qs, program, field, requirements))
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
