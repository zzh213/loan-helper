"""API 层单测:管理后台鉴权与核心接口。无需 pytest,使用 FastAPI TestClient。

使用独立临时库与固定管理口令,避免污染开发数据。
"""
import os
import sys
import tempfile

_TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP.close()
os.environ["APP_DB_PATH"] = _TMP.name
os.environ.pop("DATABASE_URL", None)
os.environ["ADMIN_TOKEN"] = "test-token-123"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app)
HDR = {"X-Admin-Token": "test-token-123"}


def test_health_ok():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_data_info_exposes_lpr():
    r = client.get("/api/data-info")
    assert r.status_code == 200
    assert r.json()["lpr_1y"] == 3.0


def test_leads_requires_admin():
    assert client.get("/api/leads").status_code == 401
    assert client.get("/api/leads", headers={"X-Admin-Token": "wrong"}).status_code == 401
    assert client.get("/api/leads", headers=HDR).status_code == 200


def test_admin_overview_requires_admin():
    assert client.get("/api/admin/overview").status_code == 401
    r = client.get("/api/admin/overview", headers=HDR)
    assert r.status_code == 200
    body = r.json()
    assert "counts" in body and "applications" in body and "leads" in body


def test_admin_token_via_query_param():
    r = client.get("/api/admin/overview?token=test-token-123")
    assert r.status_code == 200


def test_recommend_endpoint():
    payload = {"industry": "制造", "years_in_business": 3, "annual_revenue": 200,
               "credit_level": "good", "loan_amount": 60, "loan_purpose": "expansion"}
    r = client.post("/api/recommend", json=payload)
    assert r.status_code == 200
    assert len(r.json()["plans"]) >= 1


def test_recommend_personal_endpoint():
    payload = {"occupation_type": "salaried", "monthly_income": 10000, "credit_level": "good",
               "loan_amount": 20, "loan_purpose": "consumption", "preferred_term_months": 24}
    r = client.post("/api/recommend-personal", json=payload)
    assert r.status_code == 200
    assert len(r.json()["plans"]) >= 1


def test_application_lifecycle_via_api():
    payload = {"profile": {"company_name": "API测试企业", "industry": "制造",
               "years_in_business": 3, "annual_revenue": 200, "credit_level": "good",
               "loan_amount": 60, "loan_purpose": "expansion"}}
    r = client.post("/api/applications", json=payload)
    assert r.status_code == 200
    app_id = r.json()["id"]
    assert client.get(f"/api/applications/{app_id}").status_code == 200
    # 出现在管理总览中
    ov = client.get("/api/admin/overview", headers=HDR).json()
    assert any(a["id"] == app_id for a in ov["applications"])
    assert client.delete(f"/api/applications/{app_id}").status_code == 200


def test_lead_post_validates_phone():
    bad = client.post("/api/leads", json={"kind": "咨询", "phone": "123"})
    assert bad.status_code == 400
    ok = client.post("/api/leads", json={"kind": "咨询", "phone": "13800138000"})
    assert ok.status_code == 200


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
    try:
        os.unlink(_TMP.name)
    except OSError:
        pass
    sys.exit(1 if fails else 0)
