import json
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ICS_URL = "https://ics.fixtur.es/v2/arsenal.ics"

SEASON_START = datetime(2026, 8, 1, tzinfo=timezone.utc)
SEASON_END = datetime(2027, 7, 31, 23, 59, tzinfo=timezone.utc)


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

    elif key == "LOCATION":
        current["location"] = clean_text(value)

    elif key == "STATUS":
        current["status"] = clean_text(value)


fixtures = []

for event in events:

    dt = event.get("date")

    if not dt:
        continue

    dt_utc = dt.astimezone(timezone.utc)

    if not (SEASON_START <= dt_utc <= SEASON_END):
        continue

    summary = event.get("summary", "")

    if not summary:
        continue

    if " - " in summary:
        home, away = summary.split(" - ", 1)
    elif " v " in summary:
        home, away = summary.split(" v ", 1)
    else:
        continue

    fixtures.append({
        "home": home.strip(),
        "away": away.strip(),
        "utcDate": dt_utc.isoformat().replace("+00:00", "Z"),
        "location": event.get("location", ""),
        "status": event.get("status", "")
    })


fixtures.sort(key=lambda x: x["utcDate"])

with open("fixtures.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "updated": datetime.now(timezone.utc).isoformat(),
            "club": "Arsenal",
            "season": "2026/27",
            "matches": fixtures
        },
        f,
        indent=2,
        ensure_ascii=False
    )

print(f"Saved {len(fixtures)} fixtures")
