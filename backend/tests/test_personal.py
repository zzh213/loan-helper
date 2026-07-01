"""个人贷款推荐引擎单测。无需 pytest,直接 python3 运行。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import CreditLevel, OccupationType, PersonalLoanPurpose, PersonalProfile
from personal_recommender import recommend_personal


def _p(**kw):
    base = dict(
        name="张三", age=30, occupation_type=OccupationType.salaried,
        monthly_income=10000, income_type="salary", work_years=3,
        has_social_security=True, has_housing_fund=True, housing_fund_monthly=1500,
        has_house=False, has_car=False, has_insurance_policy=False,
        credit_level=CreditLevel.good, has_overdue=False, monthly_debt_payment=0,
        is_entrepreneur=False, special_identity=[],
        loan_amount=20, loan_purpose=PersonalLoanPurpose.consumption,
        preferred_term_months=24,
    )
    base.update(kw)
    return PersonalProfile(**base)


def test_returns_plans_and_tiers():
    resp = recommend_personal(_p())
    assert len(resp.plans) >= 1, "应至少返回一个方案"
    assert resp.tiers and len(resp.tiers) == 3, "应返回三档方案"


def test_plans_sorted_by_score():
    resp = recommend_personal(_p())
    scores = [pl.score for pl in resp.plans]
    assert scores == sorted(scores, reverse=True), "方案应按匹配度降序"


def test_risk_score_in_range():
    resp = recommend_personal(_p())
    assert 0 <= resp.risk.score <= 100
    assert resp.risk.grade in ("A", "B", "C", "D", "E")


def test_good_credit_beats_overdue():
    good = recommend_personal(_p(credit_level=CreditLevel.excellent)).risk.score
    bad = recommend_personal(_p(credit_level=CreditLevel.poor, has_overdue=True)).risk.score
    assert good > bad, "优质征信风控分应高于逾期用户"


def test_housing_fund_unlocks_fund_loan():
    resp = recommend_personal(_p(has_housing_fund=True, housing_fund_monthly=2000))
    names = " ".join(pl.product_name for pl in resp.plans)
    assert "公积金" in names, "缴存公积金应能匹配公积金信用贷"


def test_veteran_gets_50w_policy():
    resp = recommend_personal(_p(
        occupation_type=OccupationType.freelancer, is_entrepreneur=True,
        loan_purpose=PersonalLoanPurpose.startup, special_identity=["退役军人"]))
    vet = [s for s in resp.subsidies if "退役军人" in s.name]
    assert vet, "退役军人应匹配到专项扶持政策"
    assert "50" in vet[0].benefit, "退役军人创业担保贷额度应体现 50 万"


def test_civil_servant_low_rate():
    """公职人员应能匹配到利率下限贴合 LPR 的专属产品。"""
    resp = recommend_personal(_p(occupation_type=OccupationType.civil_servant))
    assert resp.plans, "公职人员应有匹配方案"
    assert min(pl.annual_rate_min for pl in resp.plans) <= 4.0


def test_amount_estimated_positive():
    resp = recommend_personal(_p(monthly_income=15000, loan_amount=30))
    assert resp.plans[0].estimated_amount > 0, "授信额度应为正"


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
