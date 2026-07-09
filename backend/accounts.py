"""账号体系(演示版):手机号 + 验证码登录、企业信息云端保存、企业多角色管理。

说明:真实短信下发需接入短信服务商(如阿里云/腾讯云短信),此处为本地演示实现——
验证码在服务端生成后直接返回给前端展示(仅演示环境),生产环境应改为短信下发且不回传。
"""
import json
import random
import re
import time
import uuid
from datetime import datetime

from storage import _conn

# 内存态验证码:{phone: {"code": "123456", "exp": ts}}
_OTP: dict = {}
_OTP_TTL = 300  # 5 分钟
_PHONE_RE = re.compile(r"^1[3-9]\d{9}$")
VALID_ROLES = ["法人", "财务", "经办人"]


def valid_phone(phone: str) -> bool:
    return bool(_PHONE_RE.match((phone or "").strip()))


def request_otp(phone: str) -> dict:
    """生成验证码(演示环境直接返回)。"""
    phone = (phone or "").strip()
    if not valid_phone(phone):
        return {"ok": False, "error": "请输入有效的 11 位手机号"}
    code = f"{random.randint(0, 999999):06d}"
    _OTP[phone] = {"code": code, "exp": time.time() + _OTP_TTL}
    # 仅演示:把验证码回传给前端展示。生产环境应改为短信下发且不返回。
    return {"ok": True, "demo_code": code, "expires_in": _OTP_TTL}


def verify_otp(phone: str, code: str) -> dict:
    """校验验证码,成功则创建/登录账号并签发 token。"""
    phone = (phone or "").strip()
    code = (code or "").strip()
    rec = _OTP.get(phone)
    if not rec or rec["exp"] < time.time():
        return {"ok": False, "error": "验证码已过期,请重新获取"}
    if rec["code"] != code:
        return {"ok": False, "error": "验证码不正确"}
    _OTP.pop(phone, None)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        row = conn.execute("SELECT phone FROM accounts WHERE phone = ?", (phone,)).fetchone()
        if row:
            conn.execute("UPDATE accounts SET last_login = ? WHERE phone = ?", (now, phone))
        else:
            conn.execute(
                "INSERT INTO accounts (phone, profile_json, roles_json, created_at, last_login) "
                "VALUES (?, '', '[]', ?, ?)",
                (phone, now, now),
            )
        token = "tk_" + uuid.uuid4().hex
        conn.execute(
            "INSERT INTO account_sessions (token, phone, created_at) VALUES (?, ?, ?)",
            (token, phone, now),
        )
    return {"ok": True, "token": token, "account": _account_dict(phone)}


def _account_dict(phone: str) -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT phone, profile_json, roles_json, created_at, last_login FROM accounts WHERE phone = ?",
            (phone,),
        ).fetchone()
    if not row:
        return {}
    try:
        profile = json.loads(row["profile_json"]) if row["profile_json"] else None
    except Exception:
        profile = None
    try:
        roles = json.loads(row["roles_json"]) if row["roles_json"] else []
    except Exception:
        roles = []
    masked = phone[:3] + "****" + phone[-4:]
    return {
        "phone": phone,
        "phone_masked": masked,
        "profile": profile,
        "roles": roles,
        "created_at": row["created_at"],
        "last_login": row["last_login"],
    }


def account_by_token(token: str) -> dict:
    token = (token or "").strip()
    if not token:
        return {}
    with _conn() as conn:
        row = conn.execute("SELECT phone FROM account_sessions WHERE token = ?", (token,)).fetchone()
    if not row:
        return {}
    return _account_dict(row["phone"])


def logout(token: str) -> None:
    token = (token or "").strip()
    if not token:
        return
    with _conn() as conn:
        conn.execute("DELETE FROM account_sessions WHERE token = ?", (token,))


def _phone_of(token: str) -> str:
    with _conn() as conn:
        row = conn.execute("SELECT phone FROM account_sessions WHERE token = ?", ((token or "").strip(),)).fetchone()
    return row["phone"] if row else ""


def save_profile(token: str, profile: dict) -> dict:
    phone = _phone_of(token)
    if not phone:
        return {"ok": False, "error": "登录状态已失效,请重新登录"}
    with _conn() as conn:
        conn.execute(
            "UPDATE accounts SET profile_json = ? WHERE phone = ?",
            (json.dumps(profile, ensure_ascii=False), phone),
        )
    return {"ok": True, "account": _account_dict(phone)}


def set_roles(token: str, roles: list) -> dict:
    """覆盖式保存企业多角色成员列表。每项:{name, role, phone}。"""
    phone = _phone_of(token)
    if not phone:
        return {"ok": False, "error": "登录状态已失效,请重新登录"}
    clean = []
    for r in (roles or [])[:20]:
        role = (r.get("role") or "").strip()
        if role not in VALID_ROLES:
            continue
        clean.append({
            "name": (r.get("name") or "").strip()[:20],
            "role": role,
            "phone": (r.get("phone") or "").strip()[:20],
        })
    with _conn() as conn:
        conn.execute(
            "UPDATE accounts SET roles_json = ? WHERE phone = ?",
            (json.dumps(clean, ensure_ascii=False), phone),
        )
    return {"ok": True, "account": _account_dict(phone)}
