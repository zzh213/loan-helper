"""后台可配置层:风控规则、产品库覆盖、政策库覆盖,均持久化在 settings 表。

设计目标:运营人员在后台调整打分权重、准入门槛、利率、产品启停、政策增改,
全部无需改代码、无需重启。读取时以「默认值 + 后台覆盖」合并生效。
"""
import json
from typing import Dict, List, Optional

import storage

# ---------------- 风控规则配置 ----------------
_RISK_KEY = "risk_config"

# 默认风控配置(与 risk.py 内置默认一致,作为回退)
DEFAULT_RISK_CONFIG = {
    "dim_max": {
        "credit": 24, "revenue": 15, "years": 12, "tax": 12,
        "collateral": 12, "orders": 9, "debt": 10, "industry": 6,
    },
    # 等级门槛(分数下限)
    "grade_thresholds": {"A": 85, "B": 70, "C": 55, "D": 40},
    # 额度系数表:score>=阈值 -> 系数
    "amount_multiplier": [[85, 1.15], [70, 1.0], [55, 0.85], [40, 0.7], [0, 0.55]],
    # 利率调整表:score>=阈值 -> 加/减息(百分点)
    "rate_adjustment": [[85, -0.5], [70, 0.0], [55, 0.6], [40, 1.5], [0, 3.0]],
}


def get_risk_config() -> Dict:
    """返回生效的风控配置(默认 + 后台覆盖合并)。"""
    raw = storage.get_setting(_RISK_KEY, "")
    cfg = json.loads(json.dumps(DEFAULT_RISK_CONFIG))  # deep copy
    if raw:
        try:
            override = json.loads(raw)
            for k in ("dim_max", "grade_thresholds"):
                if isinstance(override.get(k), dict):
                    cfg[k].update({kk: vv for kk, vv in override[k].items() if kk in cfg[k]})
            for k in ("amount_multiplier", "rate_adjustment"):
                if isinstance(override.get(k), list) and override[k]:
                    cfg[k] = override[k]
        except Exception:
            pass
    return cfg


def save_risk_config(cfg: Dict) -> Dict:
    """校验并保存风控配置覆盖。返回生效后的配置。"""
    clean = {"dim_max": {}, "grade_thresholds": {}}
    dm = cfg.get("dim_max", {}) or {}
    for k in DEFAULT_RISK_CONFIG["dim_max"]:
        try:
            v = int(dm.get(k, DEFAULT_RISK_CONFIG["dim_max"][k]))
            clean["dim_max"][k] = max(0, min(60, v))
        except Exception:
            clean["dim_max"][k] = DEFAULT_RISK_CONFIG["dim_max"][k]
    gt = cfg.get("grade_thresholds", {}) or {}
    for k in ("A", "B", "C", "D"):
        try:
            clean["grade_thresholds"][k] = max(0, min(100, int(gt.get(k, DEFAULT_RISK_CONFIG["grade_thresholds"][k]))))
        except Exception:
            clean["grade_thresholds"][k] = DEFAULT_RISK_CONFIG["grade_thresholds"][k]
    for k in ("amount_multiplier", "rate_adjustment"):
        if isinstance(cfg.get(k), list) and cfg[k]:
            try:
                clean[k] = [[int(a), float(b)] for a, b in cfg[k]]
            except Exception:
                pass
    storage.set_setting(_RISK_KEY, json.dumps(clean, ensure_ascii=False))
    return get_risk_config()


def reset_risk_config() -> Dict:
    storage.set_setting(_RISK_KEY, "")
    return get_risk_config()


# ---------------- 产品库后台覆盖 ----------------
_PRODUCT_KEY = "product_overrides"


def _product_overrides() -> Dict:
    raw = storage.get_setting(_PRODUCT_KEY, "")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def list_products_admin() -> List[Dict]:
    """产品库后台视图:合并默认产品与后台覆盖。"""
    from products import PRODUCTS
    ov = _product_overrides()
    out = []
    for p in PRODUCTS:
        o = ov.get(p["id"], {})
        out.append({
            "id": p["id"],
            "name": p["name"],
            "provider_type": p["provider_type"],
            "requires_collateral": p.get("requires_collateral", False),
            "min_years": p.get("min_years", 0),
            "min_annual_revenue": p.get("min_annual_revenue", 0),
            "max_amount": p.get("max_amount", 0),
            "annual_rate_min": o.get("annual_rate_min", p.get("annual_rate_min", 0)),
            "annual_rate_max": o.get("annual_rate_max", p.get("annual_rate_max", 0)),
            "min_years_eff": o.get("min_years", p.get("min_years", 0)),
            "min_revenue_eff": o.get("min_annual_revenue", p.get("min_annual_revenue", 0)),
            "enabled": o.get("enabled", True),
        })
    return out


def save_product_override(pid: str, data: Dict) -> Dict:
    from products import PRODUCTS
    if not any(p["id"] == pid for p in PRODUCTS):
        return {"ok": False, "error": "产品不存在"}
    ov = _product_overrides()
    cur = ov.get(pid, {})
    if "enabled" in data:
        cur["enabled"] = bool(data["enabled"])
    for f in ("annual_rate_min", "annual_rate_max"):
        if f in data and data[f] is not None:
            try:
                cur[f] = round(float(data[f]), 2)
            except Exception:
                pass
    for f in ("min_years", "min_annual_revenue"):
        if f in data and data[f] is not None:
            try:
                cur[f] = float(data[f])
            except Exception:
                pass
    ov[pid] = cur
    storage.set_setting(_PRODUCT_KEY, json.dumps(ov, ensure_ascii=False))
    return {"ok": True}


def apply_product_overrides(products: List[Dict]) -> List[Dict]:
    """把后台覆盖应用到产品列表(供推荐引擎使用):停用的剔除,利率/门槛覆盖。"""
    ov = _product_overrides()
    if not ov:
        return products
    out = []
    for p in products:
        o = ov.get(p["id"])
        if o is None:
            out.append(p)
            continue
        if o.get("enabled") is False:
            continue
        p2 = dict(p)
        for f in ("annual_rate_min", "annual_rate_max", "min_years", "min_annual_revenue"):
            if f in o:
                p2[f] = o[f]
        out.append(p2)
    return out


# ---------------- 政策库后台覆盖(新增/停用) ----------------
_POLICY_KEY = "policy_extra"


def list_extra_policies() -> List[Dict]:
    raw = storage.get_setting(_POLICY_KEY, "")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def add_extra_policy(data: Dict) -> Dict:
    import uuid
    extras = list_extra_policies()
    pol = {
        "id": "custom-" + uuid.uuid4().hex[:8],
        "name": (data.get("name") or "").strip()[:60],
        "category": (data.get("category") or "其他").strip()[:20],
        "authority": (data.get("authority") or "").strip()[:40],
        "benefit": (data.get("benefit") or "").strip()[:200],
        "apply_points": (data.get("apply_points") or "").strip()[:200],
        "apply_window": (data.get("apply_window") or "常年可申报").strip()[:60],
        "region": (data.get("region") or "全国通用").strip()[:40],
        "industries": data.get("industries") or ["通用"],
        "scale": data.get("scale") or ["小微"],
        "updated": (data.get("updated") or "2026-07").strip()[:10],
    }
    if not pol["name"]:
        return {"ok": False, "error": "政策名称必填"}
    extras.append(pol)
    storage.set_setting(_POLICY_KEY, json.dumps(extras, ensure_ascii=False))
    return {"ok": True, "policy": pol}


def delete_extra_policy(pid: str) -> Dict:
    extras = [p for p in list_extra_policies() if p["id"] != pid]
    storage.set_setting(_POLICY_KEY, json.dumps(extras, ensure_ascii=False))
    return {"ok": True}
