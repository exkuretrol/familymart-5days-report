#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env.deploy ]]; then
  # shellcheck disable=SC1091
  source .env.deploy
fi

: "${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN}"
: "${CLOUDFLARE_ACCOUNT_ID:?Set CLOUDFLARE_ACCOUNT_ID}"
: "${CLOUDFLARE_PAGES_PROJECT:=familymart-5days-report}"

npm run build
# The Docker sandbox is mounted noexec, so run Wrangler through node instead of the bin shim.
node node_modules/wrangler/bin/wrangler.js pages deploy dist --project-name "$CLOUDFLARE_PAGES_PROJECT" --branch main
