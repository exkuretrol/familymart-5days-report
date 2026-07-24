#!/usr/bin/env python3
"""Check whether a FamilyMart 5天5好康 report slug is already deployed.

Usage:
  python3 scripts/report_status.py 2026-07-24
Exit codes:
  0 = deployed/already present
  1 = not deployed/missing
  2 = check error
"""
from __future__ import annotations

import json
import sys
import urllib.request

BASE_URL = "https://familymart-5days-report.pages.dev"


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Hermes weekly report checker"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, resp.read().decode("utf-8", "ignore")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: report_status.py YYYY-MM-DD", file=sys.stderr)
        return 2
    slug = sys.argv[1]
    try:
        status, reports_text = fetch(f"{BASE_URL}/reports.json")
        if status != 200:
            print(f"reports.json status={status}")
            return 2
        reports = json.loads(reports_text)
        if any(r.get("slug") == slug or r.get("isoWeekStart") == slug for r in reports):
            # Also check the dated page and first image so a partial deploy does not count.
            page_status, page = fetch(f"{BASE_URL}/{slug}/")
            img_req = urllib.request.Request(f"{BASE_URL}/{slug}/images/01.jpg", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(img_req, timeout=20) as img_resp:
                img_status = img_resp.status
            if page_status == 200 and img_status == 200 and slug in page:
                print(f"DEPLOYED {slug}")
                return 0
        print(f"MISSING {slug}")
        return 1
    except Exception as exc:
        print(f"ERROR checking {slug}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
