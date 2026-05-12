import hashlib
import json
import os
import random
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
INCIDENTS_FILE          = os.path.join(DATA_DIR, "incidents.json")
NOTIFICATIONS_FILE      = os.path.join(DATA_DIR, "notifications.json")
BROADCAST_LOG_FILE      = os.path.join(DATA_DIR, "broadcast_log.json")
NEWS_FILE               = os.path.join(DATA_DIR, "news.json")
TL_ACCOUNTS_FILE        = os.path.join(DATA_DIR, "tl_accounts.json")
REVIEWER_ACCOUNTS_FILE  = os.path.join(DATA_DIR, "reviewer_accounts.json")


def _ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    for f, default in [
        (INCIDENTS_FILE, []),
        (NOTIFICATIONS_FILE, {}),
        (BROADCAST_LOG_FILE, []),
        (NEWS_FILE, []),
        (TL_ACCOUNTS_FILE, []),
        (REVIEWER_ACCOUNTS_FILE, []),
    ]:
        if not os.path.exists(f):
            with open(f, "w") as fh:
                json.dump(default, fh)


# ── Reviewer Accounts ─────────────────────────────────────────────────────────

def load_reviewer_accounts() -> list:
    _ensure_files()
    with open(REVIEWER_ACCOUNTS_FILE, "r") as f:
        return json.load(f)


def _save_reviewer_accounts(data: list):
    with open(REVIEWER_ACCOUNTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_reviewer_account(username: str, display_name: str, password: str,
                             market: str, flows: list) -> dict | None:
    accounts = load_reviewer_accounts()
    if any(a["username"] == username for a in accounts):
        return None
    account = {
        "username":      username,
        "display_name":  display_name,
        "password_hash": _hash_password(password),
        "market":        market,
        "flows":         flows,
        "created_at":    datetime.now().isoformat(),
    }
    accounts.append(account)
    _save_reviewer_accounts(accounts)
    return account


def authenticate_reviewer(username: str, password: str) -> dict | None:
    accounts = load_reviewer_accounts()
    h = _hash_password(password)
    return next(
        (a for a in accounts if a["username"] == username and a["password_hash"] == h),
        None,
    )


def seed_reviewer_accounts(market_reviewers: dict, reviewer_flows: dict):
    """Auto-create reviewer accounts for the demo. Password = username."""
    _ensure_files()
    accounts = load_reviewer_accounts()
    existing = {a["username"] for a in accounts}
    new_accounts = []
    for market, reviewers in market_reviewers.items():
        for username in reviewers:
            if username not in existing:
                flows = reviewer_flows.get(username, ["CM"])
                display = username.replace("_", " ").title()
                new_accounts.append({
                    "username":      username,
                    "display_name":  display,
                    "password_hash": _hash_password(username),
                    "market":        market,
                    "flows":         flows,
                    "created_at":    datetime.now().isoformat(),
                })
    if new_accounts:
        accounts.extend(new_accounts)
        _save_reviewer_accounts(accounts)


# ── TL Accounts ────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def load_tl_accounts() -> list:
    _ensure_files()
    with open(TL_ACCOUNTS_FILE, "r") as f:
        return json.load(f)


def _save_tl_accounts(data: list):
    with open(TL_ACCOUNTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_tl_account(username: str, display_name: str, password: str) -> dict | None:
    """Create a new TL account. Returns None if username already exists."""
    accounts = load_tl_accounts()
    if any(a["username"] == username for a in accounts):
        return None
    account = {
        "username":     username,
        "display_name": display_name,
        "password_hash": _hash_password(password),
        "created_at":   datetime.now().isoformat(),
    }
    accounts.append(account)
    _save_tl_accounts(accounts)
    return account


def authenticate_tl(username: str, password: str) -> dict | None:
    """Return the account dict if credentials match, else None."""
    accounts = load_tl_accounts()
    h = _hash_password(password)
    return next(
        (a for a in accounts if a["username"] == username and a["password_hash"] == h),
        None,
    )


def set_tl_policy_acked(username: str):
    """Mark the TL as having acknowledged the dispatch policy."""
    accounts = load_tl_accounts()
    for a in accounts:
        if a["username"] == username:
            a["policy_acked"] = True
            break
    _save_tl_accounts(accounts)


def get_tl_policy_acked(username: str) -> bool:
    accounts = load_tl_accounts()
    account = next((a for a in accounts if a["username"] == username), None)
    return bool((account or {}).get("policy_acked", False))


# ── Incidents ──────────────────────────────────────────────────────────────────

def load_incidents():
    _ensure_files()
    with open(INCIDENTS_FILE, "r") as f:
        return json.load(f)


def save_incidents(data):
    with open(INCIDENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_incident(title, description, markets, locations, flows, metric,
                    team_lead, task_number="", task_time=""):
    incidents = load_incidents()
    incident = {
        "id":                   task_number,
        "task_number":          task_number,
        "task_time":            task_time,
        "title":                title,
        "description":          description,
        "markets":              markets,    # list[str]
        "locations":            locations,  # list[str]
        "flows":                flows,      # list[str]
        "metric":               metric,     # str
        "team_lead":            team_lead,
        "created_at":           datetime.now().isoformat(),
        "updated_at":           datetime.now().isoformat(),
        "status":               "open",
        "classification":       None,
        "responses":            {},         # {reviewer: True/False} — initial impact responses
        "resolution_responses": {},         # {reviewer: True/False} — True="resolved", False="still impacted"
        "rebroadcast_history":  [],         # list of {at, target_count, sent_by}
        "last_broadcast_at":    None,       # ISO string of most recent broadcast/rebroadcast
        "remediation_actions":  [],         # list[str] — AI-suggested action steps
        "impact_analysis":      None,
        "report":               None,
    }
    incidents.append(incident)
    save_incidents(incidents)
    return incident


def get_incident(incident_id):
    return next((i for i in load_incidents() if i["id"] == incident_id), None)


def update_incident(incident_id, updates):
    incidents = load_incidents()
    for i, inc in enumerate(incidents):
        if inc["id"] == incident_id:
            incidents[i].update(updates)
            incidents[i]["updated_at"] = datetime.now().isoformat()
            save_incidents(incidents)
            return incidents[i]
    return None


def add_response(incident_id, user, affected: bool):
    incident = get_incident(incident_id)
    if not incident:
        return None
    incident["responses"][user] = affected
    return update_incident(incident_id, {"responses": incident["responses"]})


def add_resolution_response(incident_id: str, user: str, resolved: bool):
    """Record a reviewer's rebroadcast response: True=resolved, False=still impacted."""
    incident = get_incident(incident_id)
    if not incident:
        return None
    res = incident.get("resolution_responses", {})
    res[user] = resolved
    return update_incident(incident_id, {"resolution_responses": res})


def get_impacted_now(incident: dict) -> list:
    """
    Reviewers who originally reported impact AND have not yet responded 'resolved'
    in the latest rebroadcast round. This is the target list for the next rebroadcast.
    """
    responses            = incident.get("responses", {})
    resolution_responses = incident.get("resolution_responses", {})
    return [
        u for u, v in responses.items()
        if v and not resolution_responses.get(u)
    ]


def log_rebroadcast(incident_id: str, target_users: list, sent_by: str):
    """
    Stamp the incident with a rebroadcast record and update last_broadcast_at.
    Clears resolution_responses so the new round starts fresh.
    """
    incident = get_incident(incident_id)
    if not incident:
        return None
    now = datetime.now().isoformat()
    history = incident.get("rebroadcast_history", [])
    history.append({
        "at":           now,
        "target_count": len(target_users),
        "targets":      list(target_users),
        "sent_by":      sent_by,
    })
    return update_incident(incident_id, {
        "rebroadcast_history":  history,
        "last_broadcast_at":    now,
        "resolution_responses": {},   # fresh slate for this round
    })


# ── Notifications ──────────────────────────────────────────────────────────────

def load_notifications():
    _ensure_files()
    with open(NOTIFICATIONS_FILE, "r") as f:
        return json.load(f)


def save_notifications(data):
    with open(NOTIFICATIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def broadcast_to_market(incident, market_users: list, update=False):
    """Create a notification entry for each user in the market."""
    notifs = load_notifications()
    notif_type = "incident_updated" if update else "new_incident"
    label = "UPDATED" if update else "NEW"
    incident_id = incident["id"]
    markets = incident.get("markets", incident.get("market", []))
    markets_str = ", ".join(markets) if isinstance(markets, list) else markets

    for user in market_users:
        if user not in notifs:
            notifs[user] = []

        if update:
            for n in notifs[user]:
                if n.get("incident_id") == incident_id:
                    n["superseded"] = True

        notifs[user].append({
            "notif_id":            str(uuid.uuid4())[:8],
            "incident_id":         incident_id,
            "type":                notif_type,
            "label":               label,
            "title":               incident["title"],
            "description":         incident["description"],
            "market":              markets_str,
            "severity":            (incident.get("classification") or {}).get("severity", "Unknown"),
            "team_lead":           incident["team_lead"],
            "remediation_actions": incident.get("remediation_actions", []),
            "read":                False,
            "responded":           False,
            "superseded":          False,
            "created_at":          datetime.now().isoformat(),
        })

    save_notifications(notifs)


def get_user_notifications(username: str):
    notifs = load_notifications()
    return notifs.get(username, [])


def broadcast_status_check(incident: dict, target_users: list):
    """
    Send a STATUS CHECK notification to impacted reviewers after a rebroadcast.
    Supersedes any existing live notifications for the same incident.
    """
    notifs = load_notifications()
    incident_id = incident["id"]
    markets = incident.get("markets", [])
    markets_str = ", ".join(markets) if isinstance(markets, list) else markets

    for user in target_users:
        if user not in notifs:
            notifs[user] = []
        # Supersede existing live incident notifications for this incident
        for n in notifs[user]:
            if n.get("incident_id") == incident_id and not n.get("superseded"):
                n["superseded"] = True
        notifs[user].append({
            "notif_id":    str(uuid.uuid4())[:8],
            "incident_id": incident_id,
            "type":        "status_check",
            "label":       "STATUS CHECK",
            "title":       incident["title"],
            "description": incident["description"],
            "market":      markets_str,
            "severity":    (incident.get("classification") or {}).get("severity", "Unknown"),
            "team_lead":   incident["team_lead"],
            "remediation_actions": incident.get("remediation_actions", []),
            "read":        False,
            "responded":   False,
            "superseded":  False,
            "created_at":  datetime.now().isoformat(),
        })

    save_notifications(notifs)


def mark_notification_read(username: str, notif_id: str):
    notifs = load_notifications()
    for n in notifs.get(username, []):
        if n["notif_id"] == notif_id:
            n["read"] = True
    save_notifications(notifs)


def mark_notification_responded(username: str, incident_id: str):
    notifs = load_notifications()
    for n in notifs.get(username, []):
        if n.get("incident_id") == incident_id and not n.get("superseded"):
            n["responded"] = True
            n["read"] = True
    save_notifications(notifs)


def get_unread_count(username: str):
    return sum(
        1 for n in get_user_notifications(username)
        if not n["read"] and not n.get("superseded")
    )


# ── Broadcast Log ──────────────────────────────────────────────────────────────

def load_broadcast_log() -> list:
    _ensure_files()
    with open(BROADCAST_LOG_FILE, "r") as f:
        return json.load(f)


def save_broadcast_log(data: list):
    with open(BROADCAST_LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def update_broadcast_log_entries(incident_id: str, fields: dict):
    """Update all broadcast log entries matching incident_id with the given fields."""
    log = load_broadcast_log()
    for entry in log:
        if entry.get("incident_id") == incident_id:
            entry.update(fields)
    save_broadcast_log(log)


def log_broadcast(incident: dict, market_users: list, update: bool = False):
    """Append one entry to the broadcast log every time an incident is sent out."""
    log = load_broadcast_log()
    log.append({
        "log_id":         str(uuid.uuid4())[:8].upper(),
        "incident_id":    incident["id"],
        "incident_title": incident["title"],
        "markets":        incident.get("markets", []),
        "locations":      incident.get("locations", []),
        "flows":          incident.get("flows", []),
        "metric":         incident.get("metric", ""),
        "team_lead":      incident["team_lead"],
        "severity":       (incident.get("classification") or {}).get("severity", "Unknown"),
        "label":          "UPDATE" if update else "NEW",
        "reviewer_count": len(market_users),
        "reviewers":      list(market_users),
        "broadcast_at":   datetime.now().isoformat(),
        "simulated":      False,
    })
    save_broadcast_log(log)


def simulate_reviewer_responses(incident_id: str, market_users: list) -> dict:
    """
    Auto-generate random Yes/No responses from all reviewers who have not yet
    responded to this incident.  Returns a summary dict for display.
    """
    incident = get_incident(incident_id)
    if not incident:
        return {"affected": [], "not_affected": [], "skipped": []}

    existing = incident.get("responses", {})
    notifs   = load_notifications()

    affected, not_affected, skipped = [], [], []

    for user in market_users:
        if user in existing:
            skipped.append(user)
            continue
        # ~55 % chance of being affected — realistic for a real incident
        is_affected = random.random() < 0.55
        add_response(incident_id, user, is_affected)

        # Mark the matching notification as responded + read
        for n in notifs.get(user, []):
            if n["incident_id"] == incident_id and not n.get("superseded"):
                n["responded"] = True
                n["read"]      = True

        (affected if is_affected else not_affected).append(user)

    save_notifications(notifs)

    # Mark the log entry as simulated
    log = load_broadcast_log()
    for entry in log:
        if entry["incident_id"] == incident_id and not entry["simulated"]:
            entry["simulated"] = True
    save_broadcast_log(log)

    return {"affected": affected, "not_affected": not_affected, "skipped": skipped}


# ── News Broadcasts ────────────────────────────────────────────────────────────

def load_news_broadcasts() -> list:
    _ensure_files()
    with open(NEWS_FILE, "r") as f:
        return json.load(f)


def _save_news(data: list):
    with open(NEWS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_news_broadcast(title: str, description: str, market: str,
                          team_lead: str, classification: dict) -> dict:
    news_list = load_news_broadcasts()
    news = {
        "news_id":         str(uuid.uuid4())[:8].upper(),
        "title":           title,
        "description":     description,
        "market":          market,
        "team_lead":       team_lead,
        "classification":  classification,
        "created_at":      datetime.now().isoformat(),
        "acknowledged_by": [],
    }
    news_list.append(news)
    _save_news(news_list)
    return news


def broadcast_news_to_market(news: dict, market_users: list):
    """Push a news notification to each reviewer in the market."""
    notifs = load_notifications()
    cls    = news.get("classification") or {}
    for user in market_users:
        if user not in notifs:
            notifs[user] = []
        notifs[user].append({
            "notif_id":    str(uuid.uuid4())[:8],
            "news_id":     news["news_id"],
            "type":        "news",
            "label":       "NEWS",
            "title":       news["title"],
            "description": news["description"],
            "market":      news["market"],
            "risk_level":  cls.get("risk_level", "Medium"),
            "category":    cls.get("category", "Other"),
            "reasoning":   cls.get("reasoning", ""),
            "team_lead":   news["team_lead"],
            "read":        False,
            "responded":   False,
            "superseded":  False,
            "created_at":  datetime.now().isoformat(),
        })
    save_notifications(notifs)


def mark_news_acknowledged(username: str, news_id: str):
    """Mark the news notification as read and responded for this user."""
    notifs = load_notifications()
    for n in notifs.get(username, []):
        if n.get("news_id") == news_id and not n.get("superseded"):
            n["responded"] = True
            n["read"]      = True
    save_notifications(notifs)


def acknowledge_news(news_id: str, username: str):
    """Record the acknowledgment in the news broadcast record."""
    news_list = load_news_broadcasts()
    for news in news_list:
        if news["news_id"] == news_id:
            if username not in news["acknowledged_by"]:
                news["acknowledged_by"].append(username)
    _save_news(news_list)
