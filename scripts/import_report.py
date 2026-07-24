#!/usr/bin/env python3
"""Import a weekly FamilyMart 5天5好康 report into the static site.

This helper is intended for the Hermes cron job after it discovers official
post text and downloads official images.

Usage:
  python3 scripts/import_report.py \
    --slug 2026-07-31 \
    --date-range '115/7/31–8/04' \
    --source-url 'https://www.facebook.com/FamilyMart/posts/...' \
    --images-dir /tmp/fm-images \
    --post-text-file /tmp/post.txt
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "content" / "reports"

DEFAULT_TITLE = "全家 5天5好康 Weekly Report"
DEFAULT_CAMPAIGN = "【上全家練5功：5天5好康】"
DEFAULT_SOURCE_NAME = "全家FamilyMart 官方 Facebook"

DEAL_MARKER_RE = re.compile(r"[➡→]\s*([^\n]+)")
CHECK_PRODUCT_RE = re.compile(r"^[✅✓]\s*(.+?)\s*$")


def roc_date_range_from_slug(slug: str) -> str:
    dt = datetime.strptime(slug, "%Y-%m-%d")
    end = dt + timedelta(days=4)
    return f"{dt.year - 1911}/{dt.month}/{dt.day}–{end.month}/{end.day:02d}"


def parse_items(text: str) -> list[dict[str, list[str] | str]]:
    """Best-effort parse of FB post product lines.

    Groups product lines that precede a deal arrow marker. If parsing fails,
    the caller can still produce an image-first report.
    """
    items: list[dict[str, list[str] | str]] = []
    pending: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        product_match = CHECK_PRODUCT_RE.match(line)
        if product_match:
            product = product_match.group(1).strip()
            if product and not product.startswith("—"):
                pending.append(product)
            else:
                pending.append(product)
            continue
        deal_match = DEAL_MARKER_RE.search(line)
        if deal_match and pending:
            deal = deal_match.group(1).strip()
            items.append({"deal": deal, "products": pending})
            pending = []
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True, help="First day of drop, YYYY-MM-DD")
    parser.add_argument("--date-range", help="ROC date range, e.g. 115/7/31–8/04")
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--source-name", default=DEFAULT_SOURCE_NAME)
    parser.add_argument("--images-dir", required=True)
    parser.add_argument("--post-text-file")
    parser.add_argument("--items-json", help="Optional JSON file containing items array")
    args = parser.parse_args()

    slug = args.slug
    date_range = args.date_range or roc_date_range_from_slug(slug)
    images_dir = Path(args.images_dir)
    image_files = sorted([p for p in images_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}])
    if not image_files:
        raise SystemExit(f"No image files found in {images_dir}")
    # Read image bytes before clearing the destination, so re-importing an
    # existing report from its own images directory is safe.
    image_blobs = [(p.suffix.lower(), p.read_bytes()) for p in image_files]

    post_text = ""
    if args.post_text_file and Path(args.post_text_file).exists():
        post_text = Path(args.post_text_file).read_text(encoding="utf-8")

    if args.items_json:
        items = json.loads(Path(args.items_json).read_text(encoding="utf-8"))
    else:
        items = parse_items(post_text)

    report_dir = REPORTS / slug
    report_images = report_dir / "images"
    if report_images.exists():
        shutil.rmtree(report_images)
    report_images.mkdir(parents=True, exist_ok=True)

    for idx, (source_suffix, data) in enumerate(image_blobs, 1):
        # Convert extension to .jpg name if source is jpg; otherwise keep actual extension.
        suffix = ".jpg" if source_suffix in {".jpg", ".jpeg"} else source_suffix
        (report_images / f"{idx:02d}{suffix}").write_bytes(data)

    tz = timezone(timedelta(hours=8))
    report = {
        "title": DEFAULT_TITLE,
        "campaign": DEFAULT_CAMPAIGN,
        "dateRange": date_range,
        "isoWeekStart": slug,
        "sourceName": args.source_name,
        "sourceUrl": args.source_url,
        "updatedAt": datetime.now(tz).isoformat(timespec="seconds"),
        "items": items,
        "notes": ["禁止酒駕，未滿18歲禁止飲酒", "圖片與活動內容以全家官方公告為準"],
    }
    (report_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Imported {slug}: {len(image_files)} images, {len(items)} item groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
