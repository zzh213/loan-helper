#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真实数据接入管道（CSV → programs.json）。

把从【官方项目页】核实的数据填入 data/sources/*.csv，运行本脚本即可导入/更新，
并把对应项目标记为「官方核实」(provenance.verified=true) + sourceUrl + lastVerified。

流程：
  1. 打开学校官方项目页，抄录入学要求/雅思/学费/截止日期
  2. 填入 data/sources/programs_verified.csv（一行一个项目，列见模板）
  3. 运行：python3 scripts/ingest.py
  4. 校验通过则合并进 data/programs.json（按 id 覆盖更新，保留其余字段）

CSV 列：
  id,country,university,qsRank,program,field,
  a985,a211,asy,asf,ahb,            # 各院校层次建议均分门槛（留空则沿用已有/默认）
  ielts_overall,ielts_sub,
  gre_total,gre_quant,              # 不要 GRE 则留空
  background,notes,tuition,duration,timeline,
  sourceUrl,lastVerified           # 官方页 URL + 核实年月(YYYY-MM)，标记为已核实的依据
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAMS = os.path.join(ROOT, "data", "programs.json")
SOURCES_DIR = os.path.join(ROOT, "data", "sources")

REQUIRED = ["id", "country", "university", "program", "field", "sourceUrl", "lastVerified"]
VALID_FIELDS = None  # 运行时从 meta 读取


def to_int(v, default=None):
    v = (v or "").strip()
    return int(float(v)) if v else default


def to_float(v, default=None):
    v = (v or "").strip()
    return float(v) if v else default


def load_programs():
    d = json.load(open(PROGRAMS, encoding="utf-8"))
    return d


def build_requirements(row, existing):
    """合并已有 requirements 与 CSV 覆盖值（CSV 空值则保留原值）。"""
    req = dict(existing or {})
    abt = dict(req.get("avgByTier") or {})
    for key, col in [("985", "a985"), ("211", "a211"), ("双一流", "asy"),
                     ("双非", "asf"), ("海本/中外合作", "ahb")]:
        val = to_int(row.get(col))
        if val is not None:
            abt[key] = val
    if abt:
        req["avgByTier"] = abt

    io = to_float(row.get("ielts_overall"))
    isub = to_float(row.get("ielts_sub"))
    if io is not None:
        req["ielts"] = {"overall": io, "sub": isub if isub is not None else io}

    gt = to_int(row.get("gre_total"))
    if gt is not None:
        req["gre"] = {"total": gt, "quant": to_int(row.get("gre_quant"), gt)}
    elif "gre" not in req:
        req["gre"] = None

    for col in ["background", "notes"]:
        if (row.get(col) or "").strip():
            req[col] = row[col].strip()
    req.setdefault("background", "")
    req.setdefault("notes", "")
    return req


def ingest_file(path, by_id, meta):
    added = updated = errors = 0
    fields_allowed = set(meta.get("fields", []))
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            if not (row.get("id") or "").strip():
                continue
            missing = [c for c in REQUIRED if not (row.get(c) or "").strip()]
            if missing:
                print(f"  [行{i}] 跳过：缺必填列 {missing}")
                errors += 1
                continue
            if fields_allowed and row["field"].strip() not in fields_allowed:
                print(f"  [行{i}] 警告：field「{row['field']}」不在已知方向列表，仍导入")

            pid = row["id"].strip()
            existing = by_id.get(pid)
            req = build_requirements(row, (existing or {}).get("requirements"))
            entry = dict(existing or {})
            entry.update({
                "id": pid,
                "country": row["country"].strip(),
                "university": row["university"].strip(),
                "qsRank": to_int(row.get("qsRank"), entry.get("qsRank", 9999)),
                "program": row["program"].strip(),
                "field": row["field"].strip(),
                "degree": (row.get("degree") or entry.get("degree") or "硕士").strip(),
                "requirements": req,
                "tuition": (row.get("tuition") or "").strip() or entry.get("tuition", "学费见官网"),
                "duration": (row.get("duration") or "").strip() or entry.get("duration", ""),
                "timeline": (row.get("timeline") or "").strip() or entry.get("timeline", "申请时间见官网"),
            })
            q = f"{entry['university']} {entry['program']} entry requirements"
            entry["provenance"] = {
                "dataSource": "官方核实",
                "verified": True,
                "lastVerified": row["lastVerified"].strip(),
                "sourceUrl": row["sourceUrl"].strip(),
                "searchUrl": "https://www.google.com/search?q=" + q.replace(" ", "+"),
            }
            if existing:
                updated += 1
            else:
                added += 1
            by_id[pid] = entry
    return added, updated, errors


def main():
    data = load_programs()
    meta = data.get("meta", {})
    by_id = {p["id"]: p for p in data["programs"]}

    if not os.path.isdir(SOURCES_DIR):
        print("无 data/sources 目录")
        sys.exit(1)
    csvs = [os.path.join(SOURCES_DIR, f) for f in sorted(os.listdir(SOURCES_DIR))
            if f.endswith(".csv")]
    if not csvs:
        print("data/sources 下无 CSV，可先用模板 programs_verified.csv 填写官方数据")
        sys.exit(0)

    tot_a = tot_u = tot_e = 0
    for path in csvs:
        print(f"导入 {os.path.basename(path)} ...")
        a, u, e = ingest_file(path, by_id, meta)
        print(f"  新增 {a} / 更新 {u} / 错误 {e}")
        tot_a += a; tot_u += u; tot_e += e

    programs = list(by_id.values())
    data["programs"] = programs
    verified = sum(1 for p in programs if p.get("provenance", {}).get("verified"))
    meta["count"] = len(programs)
    meta["verifiedCount"] = verified
    data["meta"] = meta
    json.dump(data, open(PROGRAMS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n完成：新增 {tot_a} / 更新 {tot_u} / 错误 {tot_e}")
    print(f"当前共 {len(programs)} 个项目，其中官方已核实 {verified} 个")


if __name__ == "__main__":
    main()
