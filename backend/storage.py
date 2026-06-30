"""申请记录持久化:使用 SQLite 存储企业的贷款方案申请记录。"""
import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional

DB_PATH = os.environ.get(
    "APP_DB_PATH", os.path.join(os.path.dirname(__file__), "applications.db")
)


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                company_name TEXT,
                industry TEXT,
                loan_amount REAL,
                best_product TEXT,
                best_amount REAL,
                risk_score INTEGER,
                risk_grade TEXT,
                status TEXT DEFAULT '待提交',
                profile_json TEXT,
                result_json TEXT,
                created_at TEXT
            )
            """
        )
        cols = [r[1] for r in conn.execute("PRAGMA table_info(applications)").fetchall()]
        if "reject_reason" not in cols:
            conn.execute("ALTER TABLE applications ADD COLUMN reject_reason TEXT DEFAULT ''")
        if "manual_override" not in cols:
            conn.execute("ALTER TABLE applications ADD COLUMN manual_override INTEGER DEFAULT 0")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_players (
                player_id TEXT PRIMARY KEY,
                nickname TEXT,
                coins INTEGER DEFAULT 0,
                total_answered INTEGER DEFAULT 0,
                total_correct INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                kind TEXT,
                company_name TEXT,
                phone TEXT,
                industry TEXT,
                loan_amount REAL,
                bank TEXT,
                slot TEXT,
                note TEXT,
                status TEXT DEFAULT '待回访',
                created_at TEXT
            )
            """
        )


def save_chat_message(session_id: str, role: str, content: str) -> None:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, created_at),
        )


def get_chat_history(session_id: str) -> List[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def list_chat_sessions() -> List[dict]:
    """返回所有会话摘要(会话ID、消息数、首条用户消息、最后时间)。"""
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT session_id,
                   COUNT(*) AS message_count,
                   MAX(created_at) AS last_at
            FROM chat_messages
            GROUP BY session_id
            ORDER BY last_at DESC
            """
        ).fetchall()
        sessions = []
        for r in rows:
            first = conn.execute(
                "SELECT content FROM chat_messages WHERE session_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1",
                (r["session_id"],),
            ).fetchone()
            sessions.append({
                "session_id": r["session_id"],
                "message_count": r["message_count"],
                "last_at": r["last_at"],
                "preview": (first["content"][:30] if first else "(无内容)"),
            })
    return sessions


def delete_chat_session(session_id: str) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "DELETE FROM chat_messages WHERE session_id = ?", (session_id,)
        )
        return cur.rowcount


# 线索/预约入库(经理预约、咨询线索)
def create_lead(data: dict) -> dict:
    lead_id = uuid.uuid4().hex[:12]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "id": lead_id,
        "kind": data.get("kind", "咨询"),
        "company_name": data.get("company_name", ""),
        "phone": data.get("phone", ""),
        "industry": data.get("industry", ""),
        "loan_amount": data.get("loan_amount", 0) or 0,
        "bank": data.get("bank", ""),
        "slot": data.get("slot", ""),
        "note": data.get("note", ""),
        "status": "待回访",
        "created_at": created_at,
    }
    with _conn() as conn:
        conn.execute(
            """INSERT INTO leads (id,kind,company_name,phone,industry,loan_amount,bank,slot,note,status,created_at)
               VALUES (:id,:kind,:company_name,:phone,:industry,:loan_amount,:bank,:slot,:note,:status,:created_at)""",
            row,
        )
    return row


def list_leads() -> List[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


# 申请状态流转
VALID_STATUS = ["待提交", "已提交", "审核中", "已通过", "已拒绝", "已放款"]


def create_application(profile: dict, result: dict) -> dict:
    app_id = uuid.uuid4().hex[:12]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plans = result.get("plans", [])
    best = plans[0] if plans else {}
    risk = result.get("result_risk") or result.get("risk", {})

    row = {
        "id": app_id,
        "company_name": profile.get("company_name") or "未命名企业",
        "industry": profile.get("industry", ""),
        "loan_amount": profile.get("loan_amount", 0),
        "best_product": best.get("product_name", "暂无匹配产品"),
        "best_amount": best.get("estimated_amount", 0),
        "risk_score": risk.get("score", 0),
        "risk_grade": risk.get("grade", "-"),
        "status": "待提交",
        "profile_json": json.dumps(profile, ensure_ascii=False),
        "result_json": json.dumps(result, ensure_ascii=False),
        "created_at": created_at,
    }
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO applications
            (id, company_name, industry, loan_amount, best_product, best_amount,
             risk_score, risk_grade, status, profile_json, result_json, created_at)
            VALUES (:id, :company_name, :industry, :loan_amount, :best_product, :best_amount,
                    :risk_score, :risk_grade, :status, :profile_json, :result_json, :created_at)
            """,
            row,
        )
    return _summary(row)


def get_setting(key: str, default: str = "") -> str:
    with _conn() as conn:
        r = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return r["value"] if r else default


def set_setting(key: str, value: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )


# 状态推进节奏:demo=按分钟快速演示;real=按天真实模拟
_ADVANCE_STEPS = {
    "demo": (1, 3, 6, 10, 12),       # 分钟
    "real": (60, 1440, 4320, 10080, 14400),  # 分钟≈1h/1d/3d/7d/10d
}


def _auto_advance(conn, r: dict) -> dict:
    """未被手动改过的记录,按提交后时长+风控等级自动模拟推进申请状态。"""
    if r.get("manual_override"):
        return r
    try:
        created = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return r
    mins = (datetime.now() - created).total_seconds() / 60.0
    grade = (r.get("risk_grade") or "B").upper()
    mode = get_setting("advance_mode", "demo")
    s1, s2, s3, s4, s5 = _ADVANCE_STEPS.get(mode, _ADVANCE_STEPS["demo"])
    if mins < s1:
        status = "待提交"
    elif mins < s2:
        status = "已提交"
    elif mins < s3:
        status = "审核中"
    else:
        if grade in ("A", "B"):
            status = "已放款" if mins >= s4 else "已通过"
        elif grade == "C":
            status = "已通过" if mins < s5 else "已放款"
        else:
            status = "已拒绝"
    reject = ""
    if status == "已拒绝":
        reject = r.get("reject_reason") or "风控等级偏低,建议先优化资质再申请"
    if status != r.get("status") or reject != (r.get("reject_reason") or ""):
        conn.execute(
            "UPDATE applications SET status = ?, reject_reason = ? WHERE id = ?",
            (status, reject, r["id"]),
        )
        r["status"], r["reject_reason"] = status, reject
    return r


def list_applications() -> List[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY created_at DESC"
        ).fetchall()
        rows = [_auto_advance(conn, dict(r)) for r in rows]
    return [_summary(r) for r in rows]


def get_application(app_id: str) -> Optional[dict]:
    with _conn() as conn:
        r = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ).fetchone()
        if not r:
            return None
        r = _auto_advance(conn, dict(r))
    return {
        **_summary(r),
        "profile": json.loads(r["profile_json"]),
        "result": json.loads(r["result_json"]),
    }


def update_status(app_id: str, status: str, reject_reason: str = "") -> Optional[dict]:
    if status not in VALID_STATUS:
        return None
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE applications SET status = ?, reject_reason = ?, manual_override = 1 WHERE id = ?",
            (status, reject_reason if status == "已拒绝" else "", app_id),
        )
        if cur.rowcount == 0:
            return None
        r = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ).fetchone()
    return _summary(dict(r))


def reject_insights() -> dict:
    """聚合历史被拒原因,生成迭代优化建议,使匹配越用越准。"""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT reject_reason FROM applications WHERE status = '已拒绝' AND reject_reason != ''"
        ).fetchall()
    reasons = {}
    for r in rows:
        reasons[r[0]] = reasons.get(r[0], 0) + 1
    top = sorted(reasons.items(), key=lambda x: -x[1])
    tips = {
        "征信不达标": "下一次优先选择担保/抵押类产品,先做前置预审修复征信短板。",
        "额度过高被压": "建议把首次申请额度下调至年营收 50% 以内,通过率更高。",
        "经营年限不足": "匹配对成立年限要求低的产品,补充法人增信材料。",
        "材料不全": "导出银行成品材料并补齐纳税/流水凭证后再提交。",
        "抵押物不足": "选择纯信用银税贷,或引入担保人增信。",
        "行业受限": "关注对本行业准入更宽松的城商行/担保产品。",
        "其他": "结合前置预审报告逐项整改后再迭代申请。",
    }
    return {
        "rejected_total": len(rows),
        "reasons": [{"reason": k, "count": v, "tip": tips.get(k, tips["其他"])} for k, v in top],
    }


def calibrate_industry(industry: str) -> dict:
    """用历史申请放款数据反哺:计算该行业实际通过率,用于校准通过率展示。"""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT status FROM applications WHERE industry = ? AND status IN "
            "('已通过','已放款','已拒绝')", (industry,)
        ).fetchall()
    done = sum(1 for r in rows if r[0] in ("已通过", "已放款"))
    total = len(rows)
    if total < 3:
        return {"calibrated": False, "samples": total}
    rate = round(done / total * 100)
    return {"calibrated": True, "samples": total, "actual_pass_rate": rate,
            "delta": rate - 70}


def data_assets() -> dict:
    """沉淀的独家私有数据集统计:真实审批样本、贴息落地案例、行业分布。
    这是通用大模型无法获取的线下闭环数据,样本越多壁垒越厚。"""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT industry, status, best_amount, risk_score, result_json, created_at FROM applications"
        ).fetchall()
    total = len(rows)
    decided = [r for r in rows if r["status"] in ("已通过", "已放款", "已拒绝")]
    approved = [r for r in rows if r["status"] in ("已通过", "已放款")]
    pass_rate = round(len(approved) / len(decided) * 100) if decided else 0
    released_amt = round(sum((r["best_amount"] or 0) for r in approved), 1)
    avg_score = round(sum((r["risk_score"] or 0) for r in rows) / total) if total else 0

    subsidy_cases = 0
    subsidy_amt = 0.0
    ind = {}
    for r in rows:
        ind[r["industry"]] = ind.get(r["industry"], 0) + 1
        try:
            res = json.loads(r["result_json"] or "{}")
            subs = res.get("subsidies", []) or []
            if subs:
                subsidy_cases += 1
        except Exception:
            pass
    industries = sorted(({"name": k, "count": v} for k, v in ind.items()),
                        key=lambda x: -x["count"])[:8]
    moat = min(100, total * 4)

    monthly = {}
    for r in rows:
        m = (r["created_at"] or "")[:7] if "created_at" in r.keys() else ""
        if not m:
            continue
        d = monthly.setdefault(m, {"samples": 0, "approved": 0})
        d["samples"] += 1
        if r["status"] in ("已通过", "已放款"):
            d["approved"] += 1
    trend = [{"month": k, "samples": v["samples"], "approved": v["approved"]}
             for k, v in sorted(monthly.items())][-6:]
    return {
        "total_samples": total,
        "decided_samples": len(decided),
        "approved_samples": len(approved),
        "pass_rate": pass_rate,
        "released_amount": released_amt,
        "avg_risk_score": avg_score,
        "subsidy_cases": subsidy_cases,
        "industries": industries,
        "moat_index": moat,
        "trend": trend,
    }


def delete_application(app_id: str) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        return cur.rowcount > 0


def _summary(r: dict) -> dict:

    return {
        "id": r["id"],
        "company_name": r["company_name"],
        "industry": r["industry"],
        "loan_amount": r["loan_amount"],
        "best_product": r["best_product"],
        "best_amount": r["best_amount"],
        "risk_score": r["risk_score"],
        "risk_grade": r["risk_grade"],
        "status": r["status"],
        "reject_reason": r["reject_reason"] if "reject_reason" in r.keys() else "",
        "created_at": r["created_at"],
    }


# ------------------------- 金融闯关游戏 -------------------------
import quiz as _quizmod  # noqa: E402


def _ensure_player(conn, player_id: str) -> dict:
    r = conn.execute(
        "SELECT * FROM quiz_players WHERE player_id = ?", (player_id,)
    ).fetchone()
    if r:
        return dict(r)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO quiz_players (player_id, coins, total_answered, total_correct, best_streak, level, updated_at) "
        "VALUES (?, 0, 0, 0, 0, 1, ?)",
        (player_id, now),
    )
    return {
        "player_id": player_id, "nickname": None, "coins": 0,
        "total_answered": 0, "total_correct": 0, "best_streak": 0,
        "level": 1, "updated_at": now,
    }


def _player_payload(row: dict) -> dict:
    coins = row["coins"]
    info = _quizmod.level_info(coins)
    answered = row["total_answered"] or 0
    correct = row["total_correct"] or 0
    accuracy = round(correct / answered * 100) if answered else 0
    return {
        "player_id": row["player_id"],
        "nickname": row.get("nickname"),
        "coins": coins,
        "total_answered": answered,
        "total_correct": correct,
        "best_streak": row.get("best_streak", 0),
        "accuracy": accuracy,
        **info,
    }


def get_quiz_progress(player_id: str) -> dict:
    with _conn() as conn:
        row = _ensure_player(conn, player_id)
    return _player_payload(row)


def record_quiz_answer(player_id: str, correct: bool, coins_earned: int, streak: int) -> dict:
    """记录一次答题结果,更新金币、答对数、连胜与等级。返回最新进度。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        row = _ensure_player(conn, player_id)
        coins = row["coins"] + (coins_earned if correct else 0)
        answered = (row["total_answered"] or 0) + 1
        correct_n = (row["total_correct"] or 0) + (1 if correct else 0)
        best_streak = max(row.get("best_streak", 0) or 0, streak or 0)
        level = _quizmod.level_info(coins)["level"]
        conn.execute(
            "UPDATE quiz_players SET coins = ?, total_answered = ?, total_correct = ?, "
            "best_streak = ?, level = ?, updated_at = ? WHERE player_id = ?",
            (coins, answered, correct_n, best_streak, level, now, player_id),
        )
        row = conn.execute(
            "SELECT * FROM quiz_players WHERE player_id = ?", (player_id,)
        ).fetchone()
    return _player_payload(dict(row))


def set_quiz_nickname(player_id: str, nickname: str) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        _ensure_player(conn, player_id)
        conn.execute(
            "UPDATE quiz_players SET nickname = ?, updated_at = ? WHERE player_id = ?",
            (nickname[:20] if nickname else None, now, player_id),
        )
        row = conn.execute(
            "SELECT * FROM quiz_players WHERE player_id = ?", (player_id,)
        ).fetchone()
    return _player_payload(dict(row))


def quiz_leaderboard(limit: int = 10) -> List[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM quiz_players WHERE total_answered > 0 "
            "ORDER BY coins DESC, total_correct DESC LIMIT ?",
            (limit,),
        ).fetchall()
    board = []
    for i, r in enumerate(rows):
        p = _player_payload(dict(r))
        board.append({
            "rank": i + 1,
            "nickname": p["nickname"] or ("玩家" + p["player_id"][:4]),
            "coins": p["coins"],
            "level": p["level"],
            "title": p["title"],
            "emoji": p["emoji"],
            "accuracy": p["accuracy"],
        })
    return board
