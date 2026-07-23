#!/usr/bin/env python3
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SITE_DATA_FILE = ROOT / "site" / "data" / "citations.json"
DATA_FILE = DATA_DIR / "citations.json"
PROFILE_URL = "https://scholar.google.com/citations?user=pHrzj5kAAAAJ&hl=en"


def fetch_profile_html() -> str:
    req = urllib.request.Request(
        PROFILE_URL,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def extract_citations(html: str) -> int | None:
    patterns = [r"Cited by\s*([0-9,]+)", r'"Cited by\s*([0-9,]+)"']
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))

    meta_match = re.search(r'<meta name="description" content="([^"]*)"', html, re.IGNORECASE)
    if meta_match:
        meta = meta_match.group(1)
        m = re.search(r"Cited by\s*([0-9,]+)", meta, re.IGNORECASE)
        if m:
            return int(m.group(1).replace(",", ""))

    return None


def main() -> None:
    html = fetch_profile_html()
    citations = extract_citations(html)
    if citations is None:
        raise RuntimeError("Could not extract citation count from Scholar profile")

    data = {
        "citations": citations,
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": PROFILE_URL,
    }

    DATA_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    SITE_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    SITE_DATA_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Updated citation count to {citations}")


if __name__ == "__main__":
    main()
