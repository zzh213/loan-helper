#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四批扩充：补强薄弱方向（软件工程/通信/材料/公共政策/设计/翻译/环境/市场营销/机械/心理/土木）。
真实项目名 + 公开经验参考线（非官方保证）。去重安全、可重复运行。
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
    # ===================== 软件工程 =====================
    ("se-ic-uk", "英国", "帝国理工学院", 2, "Computing (Software Engineering) MSc", "软件工程",
     req(86, 88, 89, 90, 82, 7.0, 6.5, None, "需 CS/软件背景 + 强编程", "IC 计算系，竞争激烈")),
    ("se-ucl-uk", "英国", "伦敦大学学院 UCL", 9, "Software Systems Engineering MSc", "软件工程",
     req(82, 85, 87, 88, 78, 6.5, 6.0, None, "需 CS/工科背景", "")),
    ("se-manchester-uk", "英国", "曼彻斯特大学", 34, "Software Engineering MSc", "软件工程",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需 CS/相关背景", "")),
    ("se-nus-sg", "新加坡", "新加坡国立大学 NUS", 8, "Master of Computing (Software Engineering)", "软件工程",
     req(83, 85, 87, 88, 78, 6.5, 6.0, None, "需 CS 背景 + 工作经验优先", "")),
    ("se-cmu-us", "美国", "卡内基梅隆大学 CMU", 52, "Master of Software Engineering (MSE)", "软件工程",
     req(86, 88, 89, 90, 82, 7.0, 6.5, None, "需 CS + 2 年工作经验", "CMU 软件工程全球顶尖，重经验")),

    # ===================== 通信工程 =====================
    ("comm-ic-uk", "英国", "帝国理工学院", 2, "Communications & Signal Processing MSc", "通信工程",
     req(84, 86, 88, 89, 80, 6.5, 6.0, None, "需 EE/通信背景", "")),
    ("comm-ucl-uk", "英国", "伦敦大学学院 UCL", 9, "Wireless & Optical Communications MSc", "通信工程",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需 EE/通信背景", "")),
    ("comm-edinburgh-uk", "英国", "爱丁堡大学", 27, "Signal Processing & Communications MSc", "通信工程",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需 EE/数理背景", "")),
    ("comm-hkust-hk", "中国香港", "香港科技大学 HKUST", 47, "Telecommunications MSc", "通信工程",
     req(78, 81, 83, 85, 74, 6.5, 5.5, None, "需 EE/通信背景", "")),

    # ===================== 材料工程 =====================
    ("mat-ic-uk", "英国", "帝国理工学院", 2, "Advanced Materials Science & Engineering MSc", "材料工程",
     req(82, 85, 87, 88, 78, 6.5, 6.0, None, "需材料/化学/物理背景", "")),
    ("mat-manchester-uk", "英国", "曼彻斯特大学", 34, "Advanced Engineering Materials MSc", "材料工程",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "需材料/工科背景", "曼大材料学院（含石墨烯研究）")),
    ("mat-nus-sg", "新加坡", "新加坡国立大学 NUS", 8, "Master of Science (Materials Science & Engineering)", "材料工程",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需材料/工科背景", "")),

    # ===================== 公共政策/管理 =====================
    ("pp-lse-uk", "英国", "伦敦政治经济学院 LSE", 50, "Public Policy & Administration MSc", "公共政策/管理",
     req(83, 85, 87, 88, 79, 7.0, 6.5, None, "社科/政经背景", "LSE 公共政策声誉强")),
    ("pp-ucl-uk", "英国", "伦敦大学学院 UCL", 9, "Public Policy MSc", "公共政策/管理",
     req(80, 83, 85, 87, 76, 7.0, 6.5, None, "社科/政经背景", "")),
    ("pp-nus-sg", "新加坡", "新加坡国立大学 NUS", 8, "Master in Public Policy (LKY School)", "公共政策/管理",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "社科背景 + 实习/工作优先", "李光耀公共政策学院亚洲领先")),
    ("pp-columbia-us", "美国", "哥伦比亚大学", 34, "Master of Public Administration (SIPA)", "公共政策/管理",
     req(84, 86, 88, 89, 80, 7.0, 6.5, None, "社科背景 + 实习/工作", "哥大 SIPA")),

    # ===================== 设计/艺术 =====================
    ("design-ucl-uk", "英国", "伦敦大学学院 UCL", 9, "Design for Manufacture MArch", "设计/艺术",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "设计/建筑背景 + 作品集", "需作品集")),
    ("design-glasgow-uk", "英国", "格拉斯哥大学", 76, "Information Design MSc", "设计/艺术",
     req(74, 77, 79, 82, 70, 6.5, 6.0, None, "设计/传媒背景 + 作品集", "")),
    ("design-hkpu-hk", "中国香港", "香港理工大学", 57, "Master of Design (Interaction Design)", "设计/艺术",
     req(74, 77, 79, 82, 70, 6.5, 6.0, None, "设计背景 + 作品集", "港理工设计学院亚洲知名")),
    ("design-pratt-us", "美国", "纽约大学 NYU", 39, "Integrated Design & Media MS", "设计/艺术",
     req(76, 79, 81, 84, 72, 7.0, 6.5, None, "设计/媒体背景 + 作品集", "")),

    # ===================== 翻译/语言 =====================
    ("trans-bath-uk", "英国", "巴斯大学", 150, "Translation & Professional Language Skills MA", "翻译/语言",
     req(78, 81, 83, 85, 74, 7.0, 6.5, None, "语言/翻译背景 + 双语能力", "巴斯口译笔译全英顶尖，需通过笔试面试")),
    ("trans-ncl-uk", "英国", "纽卡斯尔大学", 129, "Translating & Interpreting MA", "翻译/语言",
     req(76, 79, 81, 84, 72, 7.0, 6.5, None, "语言/翻译背景", "纽卡口译笔译知名")),
    ("trans-cuhk-hk", "中国香港", "香港中文大学 CUHK", 36, "Master of Arts in Translation", "翻译/语言",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "语言/翻译背景", "")),

    # ===================== 环境科学 =====================
    ("env-ic-uk", "英国", "帝国理工学院", 2, "Environmental Technology MSc", "环境科学",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "环境/理工背景", "IC 环境政策学院")),
    ("env-edinburgh-uk", "英国", "爱丁堡大学", 27, "Environmental Sustainability MSc", "环境科学",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "环境/社科/理工背景", "")),
    ("env-unimelb-au", "澳大利亚", "墨尔本大学", 13, "Master of Environment", "环境科学",
     req(74, 77, 79, 82, 70, 6.5, 6.0, None, "环境/相关背景", "")),

    # ===================== 市场营销 =====================
    ("mkt-warwick-uk", "英国", "华威大学", 69, "Marketing & Strategy MSc", "市场营销",
     req(80, 83, 85, 87, 76, 7.0, 6.5, None, "商科/社科背景", "WBS 商学院")),
    ("mkt-manchester-uk", "英国", "曼彻斯特大学", 34, "Marketing MSc", "市场营销",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "商科/社科背景", "")),
    ("mkt-edinburgh-uk", "英国", "爱丁堡大学", 27, "Marketing MSc", "市场营销",
     req(78, 81, 83, 85, 74, 7.0, 6.0, None, "商科/社科背景", "")),
    ("mkt-nus-sg", "新加坡", "新加坡国立大学 NUS", 8, "Master of Science in Marketing Analytics & Insights", "市场营销",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "商科/数理背景", "")),

    # ===================== 机械工程 =====================
    ("mech-ic-uk", "英国", "帝国理工学院", 2, "Advanced Mechanical Engineering MSc", "机械工程",
     req(84, 86, 88, 89, 80, 6.5, 6.0, None, "需机械/工科背景", "")),
    ("mech-manchester-uk", "英国", "曼彻斯特大学", 34, "Mechanical Engineering Design MSc", "机械工程",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "需机械/工科背景", "")),
    ("mech-nus-sg", "新加坡", "新加坡国立大学 NUS", 8, "Master of Science (Mechanical Engineering)", "机械工程",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需机械/工科背景", "")),

    # ===================== 心理学 =====================
    ("psy-ucl-uk", "英国", "伦敦大学学院 UCL", 9, "Cognitive & Decision Sciences MSc", "心理学",
     req(82, 85, 87, 88, 78, 7.0, 6.5, None, "心理/认知/社科背景", "UCL 心理系全球顶尖")),
    ("psy-kcl-uk", "英国", "伦敦国王学院 KCL", 40, "Mental Health Studies MSc", "心理学",
     req(78, 81, 83, 85, 74, 7.0, 6.5, None, "心理/医学/社科背景", "")),
    ("psy-hku-hk", "中国香港", "香港大学 HKU", 17, "Master of Social Sciences in Psychology", "心理学",
     req(78, 81, 83, 85, 74, 7.0, 6.5, None, "心理学背景", "")),

    # ===================== 土木/建筑 =====================
    ("civ-ic-uk", "英国", "帝国理工学院", 2, "Structural Engineering MSc", "土木/建筑",
     req(84, 86, 88, 89, 80, 6.5, 6.0, None, "需土木/结构背景", "")),
    ("civ-leeds-uk", "英国", "利兹大学", 75, "Structural Engineering MSc", "土木/建筑",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "需土木/结构背景", "")),
    ("civ-unsw-au", "澳大利亚", "新南威尔士大学 UNSW", 19, "Master of Engineering Science (Civil)", "土木/建筑",
     req(72, 75, 78, 81, 68, 6.5, 6.0, None, "需土木/工科背景", "")),
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
