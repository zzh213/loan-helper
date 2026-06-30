"""核心逻辑单测:风控评分与推荐引擎。无需 pytest,直接 python3 运行。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import CreditLevel, EnterpriseProfile, LoanPurpose
from recommender import recommend
from risk import assess


def _profile(**kw):
    base = dict(
        company_name="测试", industry="制造业", years_in_business=3,
        annual_revenue=800, registered_capital=100, employees=15,
        credit_level=CreditLevel.good, has_collateral=False, collateral_value=0,
        loan_amount=200, loan_purpose=LoanPurpose.working_capital,
        preferred_term_months=24, has_tax_record=True, has_invoice=True,
        has_overdue=False, urgent=False,
    )
    base.update(kw)
    return EnterpriseProfile(**base)


def test_risk_grade_range():
    r = assess(_profile())
    assert 0 <= r["score"] <= 100
    assert r["grade"] in ("A", "B", "C", "D")


def test_good_credit_beats_poor():
    good = assess(_profile(credit_level=CreditLevel.excellent))["score"]
    poor = assess(_profile(credit_level=CreditLevel.poor, has_overdue=True))["score"]
    assert good > poor


def test_recommend_returns_plans():
    resp = recommend(_profile())
    assert len(resp.plans) >= 1
    assert resp.plans[0].score >= resp.plans[-1].score
    assert resp.tiers and len(resp.tiers) == 3


def test_high_leverage_advice():
    resp = recommend(_profile(loan_amount=900, annual_revenue=800))
    assert any("额度" in a for a in resp.personalized_advice)


def test_subsidy_has_window():
    resp = recommend(_profile())
    if resp.subsidies:
        assert resp.subsidies[0].apply_window
        assert resp.subsidies[0].updated


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
    sys.exit(1 if fails else 0)
