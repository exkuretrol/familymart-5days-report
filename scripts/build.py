from pathlib import Path
import json
import shutil
import html
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
REPORTS = CONTENT / "reports"
DIST = ROOT / "dist"
BASE_URL = "https://familymart-5days-report.pages.dev"

if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir(parents=True, exist_ok=True)


def esc(value):
    return html.escape(str(value), quote=True)


def plain_items(report):
    chunks = []
    for group in report.get("items", []):
        chunks.append(f"{group['deal']}：" + "、".join(group.get("products", [])))
    return "；".join(chunks)


def report_url(slug):
    return f"{BASE_URL}/{slug}/"


def load_reports():
    reports = []
    for report_path in REPORTS.glob("*/report.json"):
        slug = report_path.parent.name
        data = json.loads(report_path.read_text(encoding="utf-8"))
        data["slug"] = slug
        data.setdefault("isoWeekStart", slug)
        data["imageSourceDir"] = str(report_path.parent / "images")
        reports.append(data)
    return sorted(reports, key=lambda r: r.get("isoWeekStart", r["slug"]), reverse=True)


def nav_html(reports, current_slug):
    links = []
    for r in reports:
        active = " active" if r["slug"] == current_slug else ""
        links.append(
            f"<a class='report-link{active}' href='/{esc(r['slug'])}/'><span>{esc(r['dateRange'])}</span><small>{esc(r['campaign'])}</small></a>"
        )
    return "\n".join(links)


def render_report(report, reports, out_dir, image_prefix):
    image_src_dir = Path(report["imageSourceDir"])
    image_dst = out_dir / image_prefix
    image_dst.mkdir(parents=True, exist_ok=True)

    images = []
    for i, src in enumerate(sorted(image_src_dir.glob("*.jpg")), 1):
        dst_name = f"{i:02d}.jpg"
        shutil.copy2(src, image_dst / dst_name)
        images.append(f"{image_prefix}/{dst_name}")

    items_parts = []
    for group in report.get("items", []):
        products = "".join(f"<li>{esc(p)}</li>" for p in group["products"])
        items_parts.append(f"<section class='deal-card'><h3>{esc(group['deal'])}</h3><ul>{products}</ul></section>")
    items_html = "\n".join(items_parts)

    image_parts = []
    for i, src in enumerate(images, 1):
        image_parts.append(
            f"<figure class='promo'><a href='{esc(src)}'><img src='{esc(src)}' alt='5天5好康 image {i}' loading='lazy'></a><figcaption>Image {i}</figcaption></figure>"
        )
    images_html = "\n".join(image_parts)
    notes_html = "".join(f"<li>{esc(n)}</li>" for n in report.get("notes", []))
    updated = report.get("updatedAt") or datetime.now().isoformat()
    canonical = report_url(report["slug"])
    title_text = f"全家 5天5好康 {report['dateRange']}｜每週五優惠圖文整理"
    description = (
        f"全家FamilyMart 5天5好康（{report['dateRange']}）官方圖片與優惠文字整理，"
        f"依每週五首日日期分類，新到舊瀏覽。{plain_items(report)[:120]}"
    )
    og_image = f"{canonical}images/01.jpg"
    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "url": f"{BASE_URL}/",
                "name": "全家 5天5好康 Weekly Report",
                "inLanguage": "zh-Hant-TW",
            },
            {
                "@type": "WebPage",
                "@id": f"{canonical}#webpage",
                "url": canonical,
                "name": title_text,
                "description": description,
                "isPartOf": {"@id": f"{BASE_URL}/#website"},
                "datePublished": report.get("updatedAt"),
                "dateModified": updated,
                "inLanguage": "zh-Hant-TW",
                "primaryImageOfPage": {"@type": "ImageObject", "url": og_image},
            },
            {
                "@type": "ItemList",
                "name": f"全家 5天5好康優惠清單 {report['dateRange']}",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": idx + 1,
                        "name": f"{group['deal']}：{'、'.join(group.get('products', []))}",
                    }
                    for idx, group in enumerate(report.get("items", []))
                ],
            },
        ],
    }, ensure_ascii=False)

    html_doc = """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title_text}</title>
  <meta name="description" content="{description}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta name="googlebot" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="zh-Hant-TW" href="{canonical}">
  <link rel="alternate" hreflang="x-default" href="{canonical}">
  <meta property="og:site_name" content="全家 5天5好康 Weekly Report">
  <meta property="og:locale" content="zh_TW">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title_text}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:image:alt" content="全家 5天5好康 {date_range} 官方優惠圖片">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title_text}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{og_image}">
  <meta name="theme-color" content="#0066b3">
  <script type="application/ld+json">{json_ld}</script>
  <link rel="stylesheet" href="/styles.css">
</head>
<body>
  <main>
    <header class="hero">
      <p class="eyebrow">FamilyMart Weekly</p>
      <h1>{title}</h1>
      <p class="campaign">{campaign}</p>
      <p class="intro">全家便利商店每週五推出的 5天5好康優惠報告。本頁依首日日期保存官方圖片、商品名稱與優惠方案，方便搜尋與回看。</p>
      <div class="meta">
        <span>分類日期：<strong>{slug}</strong></span>
        <span>活動期間：<strong>{date_range}</strong></span>
        <span>更新：<time>{updated}</time></span>
      </div>
      <p class="source">Source: <a href="{source_url}" rel="noreferrer">{source_name}</a></p>
    </header>

    <section class="layout">
      <aside class="reports-nav" aria-label="Reports navigation">
        <h2>Reports</h2>
        <p>依首日日期新到舊排序</p>
        <nav>{nav}</nav>
      </aside>

      <div class="report-body">
        <section class="gallery" aria-label="Official image set">
          {images_html}
        </section>

        <section class="deals" aria-label="Deal summary">
          <h2>文字整理</h2>
          <div class="deal-grid">
            {items_html}
          </div>
        </section>

        <section class="notes">
          <h2>Notes</h2>
          <ul>{notes_html}</ul>
        </section>
      </div>
    </section>
  </main>
</body>
</html>
""".format(
        title=esc(report["title"]),
        title_text=esc(title_text),
        description=esc(description),
        canonical=esc(canonical),
        og_image=esc(og_image),
        json_ld=json_ld.replace("</", "<\\/"),
        date_range=esc(report["dateRange"]),
        campaign=esc(report["campaign"]),
        slug=esc(report["slug"]),
        updated=esc(updated),
        source_url=esc(report["sourceUrl"]),
        source_name=esc(report["sourceName"]),
        nav=nav_html(reports, report["slug"]),
        images_html=images_html,
        items_html=items_html,
        notes_html=notes_html,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")
    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(images)


css = ''':root {
  color-scheme: light;
  --blue: #0066b3;
  --green: #16a34a;
  --yellow: #ffd54a;
  --ink: #122033;
  --muted: #5b677a;
  --card: rgba(255,255,255,.88);
  --border: rgba(18,32,51,.12);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC", sans-serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(255,213,74,.55), transparent 32rem),
    linear-gradient(135deg, #f6fbff 0%, #eef8f2 50%, #fffdf1 100%);
}
main { max-width: 1280px; margin: 0 auto; padding: 28px 16px 56px; }
.hero {
  border: 1px solid var(--border);
  background: var(--card);
  backdrop-filter: blur(10px);
  border-radius: 28px;
  padding: clamp(24px, 5vw, 54px);
  box-shadow: 0 24px 70px rgba(8, 46, 90, .12);
}
.eyebrow { margin: 0 0 10px; color: var(--blue); font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
h1 { margin: 0; font-size: clamp(2.1rem, 7vw, 5rem); line-height: .98; }
.campaign { font-size: clamp(1.15rem, 3vw, 2rem); font-weight: 800; margin: 18px 0 10px; color: var(--green); }
.intro { max-width: 860px; font-size: 1.06rem; line-height: 1.75; color: var(--muted); margin: 0 0 18px; }
.meta { display: flex; gap: 12px; flex-wrap: wrap; color: var(--muted); }
.meta span, .source { background: rgba(255,255,255,.7); border: 1px solid var(--border); border-radius: 999px; padding: 9px 13px; }
.source { display: inline-block; margin: 14px 0 0; }
a { color: var(--blue); font-weight: 700; }
.layout { display: grid; grid-template-columns: 280px 1fr; gap: 22px; margin-top: 22px; align-items: start; }
.reports-nav { position: sticky; top: 16px; background: var(--card); border: 1px solid var(--border); border-radius: 24px; padding: 18px; box-shadow: 0 18px 50px rgba(8,46,90,.08); }
.reports-nav h2 { margin: 0 0 4px; font-size: 1.35rem; }
.reports-nav p { margin: 0 0 14px; color: var(--muted); font-size: .92rem; }
.report-link { display: block; text-decoration: none; border: 1px solid var(--border); border-radius: 16px; padding: 12px; background: rgba(255,255,255,.55); margin-top: 10px; }
.report-link span { display: block; color: var(--ink); font-weight: 900; }
.report-link small { display: block; color: var(--muted); margin-top: 4px; line-height: 1.35; }
.report-link.active { border-color: var(--blue); box-shadow: 0 0 0 3px rgba(0,102,179,.12); }
.gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; align-items: start; }
.promo { margin: 0; border: 1px solid var(--border); background: var(--card); border-radius: 24px; padding: 10px; box-shadow: 0 18px 50px rgba(8,46,90,.10); }
.promo img { width: 100%; display: block; border-radius: 17px; }
figcaption { padding: 9px 4px 2px; color: var(--muted); font-size: .92rem; text-align: center; }
.deals, .notes { margin-top: 34px; }
h2 { font-size: clamp(1.6rem, 4vw, 2.5rem); }
.deal-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 14px; }
.deal-card { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 18px; }
.deal-card h3 { margin: 0 0 10px; color: var(--blue); }
ul { margin: 0; padding-left: 1.25rem; }
li + li { margin-top: 6px; }
.notes { color: var(--muted); }
@media (max-width: 820px) {
  main { padding: 14px 10px 36px; }
  .hero, .reports-nav { border-radius: 20px; }
  .layout { grid-template-columns: 1fr; }
  .reports-nav { position: static; }
  .gallery { grid-template-columns: 1fr; }
}
'''

reports = load_reports()
if not reports:
    raise SystemExit("No reports found under content/reports/<date>/report.json")

latest = reports[0]
for r in reports:
    count = render_report(r, reports, DIST / r["slug"], "images")
    print(f"Built report {r['slug']} with {count} images")

# Root and /latest/ mirror latest report while dated pages remain browsable.
render_report(latest, reports, DIST, "images")
render_report(latest, reports, DIST / "latest", "images")
(DIST / "styles.css").write_text(css, encoding="utf-8")
public_reports = [{k: v for k, v in r.items() if k != "imageSourceDir"} for r in reports]
(DIST / "reports.json").write_text(json.dumps(public_reports, ensure_ascii=False, indent=2), encoding="utf-8")

sitemap_urls = [
    (f"{BASE_URL}/", "1.0", latest.get("isoWeekStart", latest["slug"])),
    (f"{BASE_URL}/latest/", "0.9", latest.get("isoWeekStart", latest["slug"])),
]
for r in reports:
    sitemap_urls.append((report_url(r["slug"]), "0.8", r.get("isoWeekStart", r["slug"])))
sitemap = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
for loc, priority, lastmod in sitemap_urls:
    sitemap += f"  <url><loc>{esc(loc)}</loc><lastmod>{esc(lastmod)}</lastmod><changefreq>weekly</changefreq><priority>{priority}</priority></url>\n"
sitemap += "</urlset>\n"
(DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
(DIST / "robots.txt").write_text(
    "User-agent: *\nAllow: /\nSitemap: https://familymart-5days-report.pages.dev/sitemap.xml\n",
    encoding="utf-8",
)
(DIST / "_headers").write_text(
    "/*\n  X-Robots-Tag: index, follow\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Content-Type-Options: nosniff\n",
    encoding="utf-8",
)
print(f"Built {DIST} with {len(reports)} report(s), latest={latest['slug']}")
