Weekly task: update the Cloudflare Pages site for the latest 全家FamilyMart「5天5好康」report.

Context:
- Workdir: /root/familymart-5days-pages
- Production site: https://familymart-5days-report.pages.dev/
- Reports are categorized by the first day of the drop: content/reports/YYYY-MM-DD/
- Root / and /latest/ rotate to the newest report automatically when npm run deploy is run.
- Cloudflare deploy credentials are stored in .env.deploy and scripts/deploy.sh sources it.
- Official account posts around Friday 07:30 Asia/Taipei.

Rules:
1. Determine current Asia/Taipei date and time with a terminal command. This task should only act on Friday morning Asia/Taipei. If it is not Friday or it is outside the 07:30-10:00 Asia/Taipei fallback window, return exactly nothing.
2. Let slug = current Asia/Taipei date in YYYY-MM-DD. First run `python3 scripts/report_status.py "$slug"`. If it prints DEPLOYED, return exactly nothing; do not redeploy.
3. Find the official 全家FamilyMart post for today's drop. Prefer the official Facebook post. Use fallback sources only if needed: official Instagram `familymart_tw`, official Threads `familymart_tw`, web search snippets pointing to the official Facebook post. Search terms should include combinations of:
   - `"【上全家練5功：5天5好康】"`
   - `"5天5好康" "全家FamilyMart"`
   - ROC date range for today through today+4 days, e.g. `115/7/31-8/04`
   - key official post lines when present: `"夏日補給"`, `"好康接力"`, `"上全家練5功"`
4. Verify the source is official before deploying: domain/path should be official `facebook.com/FamilyMart`, `instagram.com/familymart_tw`, or `threads.com/@familymart_tw`. If only non-official mirrors are found, do not deploy.
5. Extract/download the official image set from the source. Usually the Facebook web extraction contains five `scontent...fbcdn.net/...` image URLs. Download only the promo image set, not emoji/profile/comment images. Verify each downloaded image is a real JPEG/PNG and roughly square promo art; expect about five images.
6. Save images under a temp directory outside the report destination first, e.g. `/root/familymart-5days-pages/.work/$slug/images`. Save post text to `.work/$slug/post.txt` if available.
7. Run:
   `python3 scripts/import_report.py --slug "$slug" --source-url "$source_url" --images-dir ".work/$slug/images" --post-text-file ".work/$slug/post.txt"`
   Add `--date-range` if you confidently parsed the ROC date range.
8. Run `npm run build` and verify these files exist:
   - dist/$slug/index.html
   - dist/$slug/images/01.jpg
   - dist/sitemap.xml
   - dist/robots.txt
9. Deploy with `npm run deploy`.
10. Verify live with terminal HTTP checks using a browser User-Agent:
    - https://familymart-5days-report.pages.dev/$slug/
    - https://familymart-5days-report.pages.dev/$slug/images/01.jpg
    - https://familymart-5days-report.pages.dev/sitemap.xml
11. Final response:
    - On success, include only a concise success line and the dated report URL.
    - If no official post/images are found and this is before 09:30 Asia/Taipei, return exactly nothing so later fallback attempts can retry.
    - If no official post/images are found at or after 09:30 Asia/Taipei, report a concise failure and list the sources/queries tried.
    - If deployed already, return exactly nothing.

Do not ask the user questions. Do not use unofficial images if official images are unavailable.
