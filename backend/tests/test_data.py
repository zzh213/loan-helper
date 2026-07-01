"""数据一致性与辅助逻辑单测:行业识别、个人政策、LPR 对齐、产品完整性。无需 pytest。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import lpr_reference as lp
from industry_classify import classify, classify_by_keyword
from models import CreditLevel, OccupationType, PersonalLoanPurpose, PersonalProfile
from personal_policies import match_personal_policies
from personal_products import PERSONAL_PRODUCTS
from products import PRODUCTS


def test_lpr_constants_consistent():
    assert lp.LPR_1Y == 3.0 and lp.LPR_5Y == 3.5
    assert lp.PRIVATE_LENDING_CAP == round(4 * lp.LPR_1Y, 2) == 12.0
    assert str(lp.LPR_1Y) in lp.DATA_SOURCE_NOTE


def test_policy_product_rates_not_below_lpr():
    """政策/贴息类产品利率下限不应低于当前一年期 LPR。"""
    policy_ids = {"puhui", "mortgage-biz", "gov-guarantee-loan",
                  "agri-huinong-loan", "startup-guarantee-biz"}
    for p in PRODUCTS:
        if p["id"] in policy_ids:
            assert p["annual_rate_min"] >= lp.LPR_1Y, f"{p['id']} 利率下限低于 LPR"


def test_products_have_required_fields():
    for p in PRODUCTS + PERSONAL_PRODUCTS:
        for field in ("id", "name", "annual_rate_min", "annual_rate_max"):
            assert field in p, f"产品 {p.get('id')} 缺字段 {field}"
        assert p["annual_rate_min"] <= p["annual_rate_max"], f"{p['id']} 利率区间倒置"


def test_product_ids_unique():
    for pool, label in ((PRODUCTS, "企业"), (PERSONAL_PRODUCTS, "个人")):
        ids = [p["id"] for p in pool]
        assert len(ids) == len(set(ids)), f"{label}产品 id 有重复"


def test_classify_keyword_manufacturing():
    cat, score = classify_by_keyword("做五金零件加工厂,有车床和冲压设备")
    assert cat == "制造业" and score >= 2


def test_classify_returns_valid_structure():
    r = classify("开了个奶茶店做餐饮")
    assert set(r.keys()) == {"category", "label", "method"}
    assert r["category"]
    assert r["method"] in ("ai", "keyword", "default")


def test_classify_empty_defaults():
    r = classify("")
    assert r["method"] == "default"


def _p(**kw):
    base = dict(
        age=30, occupation_type=OccupationType.freelancer, monthly_income=8000,
        income_type="business", work_years=2, has_social_security=False,
        has_housing_fund=False, credit_level=CreditLevel.good, is_entrepreneur=True,
        special_identity=[], loan_amount=15, loan_purpose=PersonalLoanPurpose.startup,
        preferred_term_months=24,
    )
    base.update(kw)
    return PersonalProfile(**base)


def test_veteran_policy_50w():
    items = match_personal_policies(_p(special_identity=["退役军人"]))
    vet = [s for s in items if "退役军人" in s.name]
    assert vet and "50" in vet[0].benefit


def test_graduate_policy_matched():
    items = match_personal_policies(_p(special_identity=["高校毕业生"]))
    assert any("毕业生" in s.name or "创业" in s.name for s in items)


def test_all_policies_have_window():
    items = match_personal_policies(_p(special_identity=["退役军人", "高校毕业生"]))
    for s in items:
        assert s.apply_window, f"政策 {s.name} 缺少申报窗口"
        assert s.authority, f"政策 {s.name} 缺少主管部门"


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                fails += 1
                print(f"FAIL {name}: {e}")
            except Exception as e:  # noqa: BLE001
                fails += 1
                print(f"ERROR {name}: {type(e).__name__}: {e}")
    sys.exit(1 if fails else 0)
