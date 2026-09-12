import json
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ICS_URL = "https://ics.fixtur.es/v2/arsenal.ics"


def clean_text(text):
    return (
        text.replace("\\n", " ")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
        .strip()
    )


def parse_datetime(key, value):
    value = value.strip()

    if value.endswith("Z"):
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ")
        return dt.replace(tzinfo=timezone.utc)

    timezone_name = None

    if "TZID=" in key:
        timezone_name = key.split("TZID=", 1)[1].split(";", 1)[0].split(":", 1)[0]

    if "T" in value:
        dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
    else:
        dt = datetime.strptime(value, "%Y%m%d")

    if timezone_name:
        try:
            return dt.replace(tzinfo=ZoneInfo(timezone_name))
        except Exception:
            pass

    return dt.replace(tzinfo=timezone.utc)


request = urllib.request.Request(
    ICS_URL,
    headers={"User-Agent": "Mozilla/5.0"}
)

raw = urllib.request.urlopen(request).read().decode("utf-8", errors="ignore")

# Join folded ICS lines
lines = []

for line in raw.splitlines():
    if line.startswith((" ", "\t")) and lines:
        lines[-1] += line[1:]
    else:
        lines.append(line)

events = []
current = None

for line in lines:

    if line == "BEGIN:VEVENT":
        current = {}
        continue

    if line == "END:VEVENT":
        if current:
            events.append(current)
        current = None
        continue

    if current is None or ":" not in line:
        continue

    key, value = line.split(":", 1)

    if key.startswith("DTSTART"):
        current["date"] = parse_datetime(key, value)

    elif key == "SUMMARY":
        current["summary"] = clean_text(value)

    elif key == "DESCRIPTION":
        current["description"] = clean_text(value)

    elif key == "LOCATION":
        current["location"] = clean_text(value)

    elif key == "STATUS":
        current["status"] = clean_text(value)


fixtures = []

for event in events:

    summary = event.get("summary", "")

    if not summary:
        continue

    # Fixtur.es normally uses "Home - Away"
    if " - " in summary:
        home, away = summary.split(" - ", 1)
    elif " v " in summary:
        home, away = summary.split(" v ", 1)
    else:
        home = summary
        away = ""

    dt = event.get("date")

    if dt:
        utc_date = dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        utc_date = None

    fixtures.append({
        "home": home.strip(),
        "away": away.strip(),
        "utcDate": utc_date,
        "competition": event.get("description", ""),
        "location": event.get("location", ""),
        "status": event.get("status", "")
    })


fixtures.sort(key=lambda x: x["utcDate"] or "")

with open("fixtures.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "updated": datetime.now(timezone.utc).isoformat(),
            "club": "Arsenal",
            "matches": fixtures
        },
        f,
        indent=2,
        ensure_ascii=False
    )

print(f"Saved {len(fixtures)} fixtures")
