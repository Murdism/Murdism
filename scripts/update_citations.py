#!/usr/bin/env python3
import json
import re
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SITE_DATA_FILE = ROOT / "site" / "data" / "citations.json"
DATA_FILE = DATA_DIR / "citations.json"
PROFILE_URL = "https://scholar.google.com/citations?user=pHrzj5kAAAAJ&hl=en"


def fetch_profile_html() -> tuple[str | None, str | None]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://scholar.google.com/",
    }

    last_error: str | None = None
    for attempt in range(3):
        req = urllib.request.Request(PROFILE_URL, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as response:
                return response.read().decode("utf-8", errors="ignore"), None
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason}"
        except Exception as exc:  # pragma: no cover - defensive fallback
            last_error = str(exc)

        if attempt < 2:
            time.sleep(2 * (attempt + 1))

    return None, last_error


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


def load_previous_data() -> dict | None:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def main() -> None:
    html, error = fetch_profile_html()
    citations = None
    status = "updated"

    if html is not None:
        citations = extract_citations(html)

    if citations is None:
        previous = load_previous_data()
        citations = previous.get("citations") if previous else None
        if citations is None:
            citations = 0
        status = "fallback"
        print(f"Using fallback citation count {citations} due to fetch issue: {error or 'unknown error'}")
    else:
        print(f"Updated citation count to {citations}")

    data = {
        "citations": citations,
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": PROFILE_URL,
        "status": status,
    }
    if error:
        data["last_error"] = error

    DATA_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    SITE_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    SITE_DATA_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
