import json
import re
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://www.arsenal.com/fixtures"

req = urllib.request.Request(
    URL,
    headers={"User-Agent": "Mozilla/5.0"}
)

html = urllib.request.urlopen(req).read().decode("utf-8", errors="ignore")

matches = []

pattern = re.compile(
    r'([A-Z][A-Za-z .&\'-]+)\s+v\s+([A-Z][A-Za-z .&\'-]+)',
    re.IGNORECASE
)

for match in pattern.finditer(html):
    home = match.group(1).strip()
    away = match.group(2).strip()

    if "Arsenal" not in home and "Arsenal" not in away:
        continue

    matches.append({
        "home": home,
        "away": away
    })

with open("fixtures.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "updated": datetime.now(ZoneInfo("UTC")).isoformat(),
            "matches": matches
        },
        f,
        indent=2
    )

print(f"Saved {len(matches)} fixtures")
