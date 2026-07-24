# FamilyMart 5天5好康 Weekly Report

Static Cloudflare Pages site for the latest weekly 全家「5天5好康」report.

## Rotation model

The report rotates by overwriting:

- `/` — latest report
- `/latest/` — latest report alias

No ZIP download is included. Images are hosted as local page assets under `/images/`.

## Update a week

1. Replace files in `content/current-images/` with the newest official images as `01.jpg`, `02.jpg`, ...
2. Edit `content/report.json`
3. Run `npm run build`

## Deploy via Cloudflare Pages Direct Upload

Set:

```bash
export CLOUDFLARE_API_TOKEN='...'
export CLOUDFLARE_ACCOUNT_ID='...'
export CLOUDFLARE_PAGES_PROJECT='familymart-5days-report'
```

Then run:

```bash
npm run deploy
```
