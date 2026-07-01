"""存储层单测(SQLite 路径,使用独立临时库)。无需 pytest。

运行前会把 APP_DB_PATH 指向临时文件,确保与开发库隔离。
"""
import os
import sys
import tempfile

_TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP.close()
os.environ["APP_DB_PATH"] = _TMP.name
os.environ.pop("DATABASE_URL", None)  # 强制走 SQLite

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import storage  # noqa: E402

storage.init_db()


def _mk_app(name="甲企业", industry="制造", grade="B", score=72):
    return storage.create_application(
        {"company_name": name, "industry": industry, "loan_amount": 100},
        {"plans": [{"product_name": "普惠贷", "estimated_amount": 80}],
         "risk": {"score": score, "grade": grade},
         "subsidies": [{"name": "贴息"}]},
    )


def test_create_and_get_application():
    a = _mk_app()
    assert a["id"]
    got = storage.get_application(a["id"])
    assert got["company_name"] == "甲企业"
    assert got["profile"]["industry"] == "制造"
    assert "plans" in got["result"]


def test_list_and_delete():
    before = len(storage.list_applications())
    a = _mk_app(name="待删企业")
    assert len(storage.list_applications()) == before + 1
    assert storage.delete_application(a["id"]) is True
    assert len(storage.list_applications()) == before


def test_status_flow_and_reject_reason():
    a = _mk_app()
    upd = storage.update_status(a["id"], "已拒绝", "征信不达标")
    assert upd["status"] == "已拒绝"
    got = storage.get_application(a["id"])
    assert got["reject_reason"] == "征信不达标"


def test_invalid_status_rejected():
    a = _mk_app()
    assert storage.update_status(a["id"], "不存在的状态") is None


def test_settings_roundtrip():
    storage.set_setting("advance_mode", "real")
    assert storage.get_setting("advance_mode") == "real"
    storage.set_setting("advance_mode", "demo")
    assert storage.get_setting("advance_mode") == "demo"
    assert storage.get_setting("nonexistent", "缺省") == "缺省"


def test_chat_history():
    storage.save_chat_message("sess-x", "user", "你好")
    storage.save_chat_message("sess-x", "assistant", "您好,请问贷款需求?")
    hist = storage.get_chat_history("sess-x")
    assert len(hist) == 2
    assert hist[0]["role"] == "user"
    assert storage.delete_chat_session("sess-x") == 2
    assert storage.get_chat_history("sess-x") == []


def test_leads_crud_and_phone():
    n0 = len(storage.list_leads())
    storage.create_lead({"kind": "预约", "company_name": "L公司", "phone": "13800138000",
                         "industry": "制造", "loan_amount": 50, "bank": "工行", "slot": "上午"})
    leads = storage.list_leads()
    assert len(leads) == n0 + 1
    assert leads[0]["phone"] == "13800138000"


def test_quiz_progress_and_leaderboard():
    storage.get_quiz_progress("player-q")
    storage.record_quiz_answer("player-q", True, 10, 1)
    storage.record_quiz_answer("player-q", False, 10, 0)
    prog = storage.get_quiz_progress("player-q")
    assert prog["coins"] == 10
    assert prog["total_answered"] == 2
    assert prog["total_correct"] == 1
    storage.set_quiz_nickname("player-q", "阿强")
    board = storage.quiz_leaderboard()
    assert any(row["nickname"] == "阿强" for row in board)


def test_reject_insights_and_assets():
    a = _mk_app(name="资产企业", grade="A")
    storage.update_status(a["id"], "已放款")
    assets = storage.data_assets()
    assert assets["total_samples"] >= 1
    assert 0 <= assets["pass_rate"] <= 100
    insights = storage.reject_insights()
    assert "rejected_total" in insights


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
