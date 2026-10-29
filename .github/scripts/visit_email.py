"""Emails a short summary of each new visit to aryanh.dev.

Runs hourly from GitHub Actions. GoatCounter allows one export an hour, so
each run exports every page view and event since the last run, groups them
by session, and sends one email per visit. Visits whose last hit is under
ten minutes old are held until the next run so a visit that straddles the
export doesn't arrive as two emails.

State (last exported hit id and held rows) lives in state.json, carried
between runs by the Actions cache.

Env: GOATCOUNTER_TOKEN, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, optional
NOTIFY_TO (defaults to GMAIL_ADDRESS) and DRY_RUN=1 to print instead of send.
"""

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


def send(subject, body):
    if os.environ.get("DRY_RUN"):
        print("=" * 60, "\nSubject:", subject, "\n" + body)
        return
    msg = EmailMessage()
    msg["From"] = os.environ["GMAIL_ADDRESS"]
    msg["To"] = os.environ.get("NOTIFY_TO") or os.environ["GMAIL_ADDRESS"]
    msg["Subject"] = subject
    msg.set_content(body + "\nStats: " + SITE + "\n")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        s.send_message(msg)


def main():
    state = {"last_hit_id": None, "held": []}
    if os.path.exists(STATE_FILE):
        state.update(json.load(open(STATE_FILE)))

    if os.environ.get("EXPORT_CSV"):  # local testing against a downloaded export
        rows, last = list(csv.DictReader(open(os.environ["EXPORT_CSV"]))), state["last_hit_id"]
        for r in rows:
            r["Path"] = r.pop("2Path", r.get("Path", ""))
    else:
        rows, last = export_since(state["last_hit_id"])
    first_run = state["last_hit_id"] is None and not os.environ.get("EXPORT_CSV")

    sessions = OrderedDict()
    for r in state["held"] + rows:
        if r.get("Bot", "0") not in ("0", ""):
            continue
        sessions.setdefault(r["Session"] or r["Date"], []).append(r)

    now = datetime.now(timezone.utc)
    held, sent = [], 0
    for rows_ in sessions.values():
        rows_.sort(key=lambda r: r["Date"])
        latest = datetime.fromisoformat(rows_[-1]["Date"].replace("Z", "+00:00"))
        if now - latest < SETTLE:
            held.extend(rows_)
            continue
        if first_run:
            continue  # don't email the whole history the first time
        send(*summarize(rows_))
        sent += 1

    json.dump({"last_hit_id": last, "held": held}, open(STATE_FILE, "w"))
    print(f"{len(rows)} new rows, {sent} emails sent, {len(held)} rows held"
          + (" (first run, history skipped)" if first_run else ""))


if __name__ == "__main__":
    sys.exit(main())
