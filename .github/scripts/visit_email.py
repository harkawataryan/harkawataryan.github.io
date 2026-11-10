"""Backup for the live visit log on the Concertify server.

The server emails each visit to aryanh.dev about 90 seconds after it ends.
This job runs hourly from GitHub Actions as a backup: it keeps the encrypted
GoatCounter-based visit log up to date, and it only sends emails itself when
the live server reports that it isn't emailing (down, asleep past the
timeout, or not configured). LIVE_STATUS_URL points at that check.

GoatCounter allows one export an hour, so
each run exports every page view and event since the last run, groups them
by session, and sends one email per visit. Visits whose last hit is under
ten minutes old are held until the next run so a visit that straddles the
export doesn't arrive as two emails.

State (last exported hit id and held rows) lives in state.json, carried
between runs by the Actions cache.

Every finished visit is also kept in a visit log for the /stats/ dashboard.
The log is encrypted with a key derived from GOATCOUNTER_TOKEN (PBKDF2 +
AES-GCM) and published by the workflow to the visit-data branch, where the
dashboard fetches it and decrypts it in the browser with the same token. The
first run without a log exports the full history once to backfill it.

Env: GOATCOUNTER_TOKEN, NOTIFY_TO (where emails go), and either
RESEND_API_KEY (sends through resend.com) or GMAIL_ADDRESS plus
GMAIL_APP_PASSWORD. DRY_RUN=1 prints instead of sending.
"""

import base64
import csv
import gzip
import io
import json
import os
import smtplib
import sys
import time
import urllib.request
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from zoneinfo import ZoneInfo

SITE = "https://aryanh.goatcounter.com"
STATE_FILE = os.environ.get("STATE_FILE", "state.json")
VISITS_FILE = os.environ.get("VISITS_FILE", "")
KDF_ITERATIONS = 200_000
MAX_VISITS = 5000
SETTLE = timedelta(minutes=10)
LOCAL_TZ = ZoneInfo("America/Chicago")

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "Washington DC", "FL": "Florida",
    "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
COUNTRIES = {
    "US": "United States", "CA": "Canada", "MX": "Mexico", "GB": "United Kingdom", "IE": "Ireland",
    "DE": "Germany", "FR": "France", "NL": "Netherlands", "CH": "Switzerland", "ES": "Spain",
    "IT": "Italy", "SE": "Sweden", "PL": "Poland", "IN": "India", "CN": "China", "JP": "Japan",
    "KR": "South Korea", "SG": "Singapore", "TW": "Taiwan", "HK": "Hong Kong", "AU": "Australia",
    "BR": "Brazil", "IL": "Israel", "AE": "UAE", "PK": "Pakistan", "VN": "Vietnam", "PH": "Philippines",
}


def api(method, path, body=None):
    req = urllib.request.Request(
        SITE + "/api/v0" + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + os.environ["GOATCOUNTER_TOKEN"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def export_since(last_hit_id):
    body = {"format": "csv"}
    if last_hit_id:
        body["start_from_hit_id"] = last_hit_id + 1
    job = json.loads(api("POST", "/export", body))
    for _ in range(60):
        status = json.loads(api("GET", f"/export/{job['id']}"))
        if status.get("error"):
            raise RuntimeError(status["error"])
        if status.get("finished_at"):
            break
        time.sleep(5)
    else:
        raise RuntimeError("export did not finish")
    raw = api("GET", f"/export/{job['id']}/download")
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    # The first header is "2Path" (the export format version is prefixed).
    for r in rows:
        r["Path"] = r.pop("2Path", r.get("Path", ""))
    return rows, status.get("last_hit_id") or last_hit_id


def place(code):
    if not code:
        return "Unknown location"
    country, _, region = code.partition("-")
    if country == "US" and region in US_STATES:
        return f"{US_STATES[region]}, US"
    name = COUNTRIES.get(country, country)
    return f"{region}, {name}" if region else name


def device(size):
    try:
        width = int(size.split(",")[0])
    except (ValueError, AttributeError):
        return "unknown screen"
    if width == 0:
        return "unknown screen"
    kind = "phone" if width < 700 else "tablet" if width < 1100 else "desktop"
    return f"{kind}, {width}px wide"


def summarize(rows):
    first = rows[0]
    pages = OrderedDict()
    sections, clicks = [], []
    for r in rows:
        path = r["Path"]
        if r["Event"] == "1":
            if path.startswith("visit/"):
                parts = path.split("/")
                sections.append((parts[1] if len(parts) > 1 else "?", parts[2] if len(parts) > 2 else "?"))
            elif path.startswith("click/"):
                clicks.append(path[len("click/"):])
            else:
                clicks.append(path)
        else:
            pages[path] = True

    when = datetime.fromisoformat(first["Date"].replace("Z", "+00:00")).astimezone(LOCAL_TZ)
    where = place(first["Location"])
    ref = first["Referrer"] or "direct (typed or bookmarked)"
    if sections:
        deepest, spent = sections[-1]
        engagement = f"scrolled to {deepest}, stayed {spent}"
    else:
        engagement = "no scroll data (left before it was sent, or blocked)"

    lines = [
        f"When:      {when:%a %b %-d, %-I:%M %p} Central",
        f"Where:     {where}",
        f"From:      {ref}",
        f"Device:    {first['Browser'] or '?'} on {first['System'].strip() or '?'}, {device(first['Screen size'])}",
        f"Visitor:   {'first visit' if first['FirstVisit'] == '1' else 'returning'}",
        f"Pages:     {', '.join(pages) or '(events only)'}",
        f"Reached:   {engagement}",
        f"Clicked:   {', '.join(clicks) if clicks else 'nothing'}",
    ]
    short_ref = first["Referrer"].split("/")[0] if first["Referrer"] else "direct"
    subject = f"aryanh.dev visit · {where} · {short_ref}"
    return subject, "\n".join(lines) + "\n"


def live_server_emails():
    """When the live server is emailing visits itself, the time it started
    recording them. Visits from before then only GoatCounter saw, so this
    job still emails those. None means this job emails everything. The free
    Render instance can take most of a minute to wake, so the timeout is
    generous."""
    url = os.environ.get("LIVE_STATUS_URL")
    if not url:
        return None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "aryanh-visit-email"}), timeout=90) as r:
            status = json.loads(r.read())
    except Exception as e:  # down or unreachable: this job sends instead
        print(f"live server check failed ({e}); sending emails from here")
        return None
    if not status.get("email"):
        return None
    since = status.get("since")
    return datetime.fromisoformat(since.replace("Z", "+00:00")) if since else datetime.min.replace(tzinfo=timezone.utc)


def send(subject, body):
    if os.environ.get("DRY_RUN"):
        print("=" * 60, "\nSubject:", subject, "\n" + body)
        return
    to = os.environ.get("NOTIFY_TO") or os.environ.get("GMAIL_ADDRESS")
    text = body + "\nStats: " + SITE + "\n"
    if os.environ.get("RESEND_API_KEY"):
        # Without a verified domain, Resend only delivers from its onboarding
        # address to the email the Resend account was created with.
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            method="POST",
            data=json.dumps({"from": "aryanh.dev <onboarding@resend.dev>", "to": [to], "subject": subject, "text": text}).encode(),
            headers={"Authorization": "Bearer " + os.environ["RESEND_API_KEY"], "Content-Type": "application/json",
                     "User-Agent": "aryanh-visit-email"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
        return
    msg = EmailMessage()
    msg["From"] = os.environ["GMAIL_ADDRESS"]
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        s.send_message(msg)


def visit_record(rows):
    """One visit as the dashboard reads it: who, from where, and every hit."""
    first = rows[0]
    try:
        width = int((first["Screen size"] or "0").split(",")[0])
    except ValueError:
        width = 0
    return {
        "id": first["Session"] or first["Date"],
        "start": rows[0]["Date"],
        "end": rows[-1]["Date"],
        "loc": first["Location"],
        "ref": first["Referrer"],
        "browser": first["Browser"],
        "system": first["System"].strip(),
        "width": width,
        "first": first["FirstVisit"] == "1",
        "hits": [{"t": r["Date"], "p": r["Path"], "e": r["Event"] == "1"} for r in rows],
    }


def _key(salt):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=KDF_ITERATIONS)
    return kdf.derive(os.environ["GOATCOUNTER_TOKEN"].encode())


def load_visits():
    """The existing log, or None when there isn't one yet (first run)."""
    if not VISITS_FILE or not os.path.exists(VISITS_FILE) or os.path.getsize(VISITS_FILE) == 0:
        return None
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    box = json.load(open(VISITS_FILE))
    salt, iv, ct = (base64.b64decode(box[k]) for k in ("salt", "iv", "ct"))
    return json.loads(AESGCM(_key(salt)).decrypt(iv, ct, None))


def save_visits(visits):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(_key(salt)).encrypt(iv, json.dumps(visits, separators=(",", ":")).encode(), None)
    b64 = lambda b: base64.b64encode(b).decode()
    box = {"v": 1, "kdf": "PBKDF2-SHA256", "iter": KDF_ITERATIONS, "salt": b64(salt), "iv": b64(iv), "ct": b64(ct),
           "updated": datetime.now(timezone.utc).isoformat()}
    json.dump(box, open(VISITS_FILE, "w"))


def merge_visit(log, rec):
    """Adds a visit, merging into an existing one with the same session."""
    for i, old in enumerate(log):
        if old["id"] == rec["id"]:
            seen = {(h["t"], h["p"]) for h in old["hits"]}
            hits = old["hits"] + [h for h in rec["hits"] if (h["t"], h["p"]) not in seen]
            hits.sort(key=lambda h: h["t"])
            log[i] = {**old, "hits": hits, "start": hits[0]["t"], "end": hits[-1]["t"]}
            return
    log.append(rec)


def main():
    state = {"last_hit_id": None, "held": []}
    if os.path.exists(STATE_FILE):
        state.update(json.load(open(STATE_FILE)))

    visits = load_visits() if VISITS_FILE else []
    backfill = VISITS_FILE and visits is None and state["last_hit_id"] is not None
    if visits is None:
        visits = []

    if os.environ.get("EXPORT_CSV"):  # local testing against a downloaded export
        rows, last = list(csv.DictReader(open(os.environ["EXPORT_CSV"]))), state["last_hit_id"]
        for r in rows:
            r["Path"] = r.pop("2Path", r.get("Path", ""))
    elif backfill:
        # No visit log yet: export everything once to build it. Only visits
        # newer than the previous run get emailed, judged by time since the
        # export rows carry no hit ids.
        rows, last = export_since(None)
    else:
        rows, last = export_since(state["last_hit_id"])
    first_run = state["last_hit_id"] is None and not os.environ.get("EXPORT_CSV")

    now = datetime.now(timezone.utc)
    prev_run = datetime.fromisoformat(state["last_run"]) if state.get("last_run") else now - timedelta(minutes=70)
    email_after = prev_run - SETTLE

    live_since = live_server_emails()
    if live_since:
        print(f"live server is emailing visits since {live_since:%Y-%m-%d %H:%M} UTC; emailing only older ones from here")

    sessions = OrderedDict()
    held_ids = {r["Session"] for r in state["held"]}
    for r in (rows if backfill else state["held"] + rows):
        if r.get("Bot", "0") not in ("0", ""):
            continue
        sessions.setdefault(r["Session"] or r["Date"], []).append(r)

    held, sent = [], 0
    for sid, rows_ in sessions.items():
        rows_.sort(key=lambda r: r["Date"])
        latest = datetime.fromisoformat(rows_[-1]["Date"].replace("Z", "+00:00"))
        if now - latest < SETTLE:
            held.extend(rows_)
            continue
        if VISITS_FILE:
            merge_visit(visits, visit_record(rows_))
        if first_run:
            continue  # don't email the whole history the first time
        if backfill and latest < email_after and sid not in held_ids:
            continue  # already emailed by an earlier run
        started = datetime.fromisoformat(rows_[0]["Date"].replace("Z", "+00:00"))
        if live_since and started >= live_since:
            continue  # the live server saw and emailed this one
        send(*summarize(rows_))
        sent += 1

    json.dump({"last_hit_id": last, "held": held, "last_run": now.isoformat()}, open(STATE_FILE, "w"))
    if VISITS_FILE:
        visits.sort(key=lambda v: v["start"])
        save_visits(visits[-MAX_VISITS:])
    print(f"{len(rows)} new rows, {sent} emails sent, {len(held)} rows held, {len(visits)} visits logged"
          + (" (first run, history skipped)" if first_run else "")
          + (" (visit log backfilled)" if backfill else ""))


if __name__ == "__main__":
    sys.exit(main())
