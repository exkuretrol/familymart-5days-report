#!/usr/bin/env bash
set -euo pipefail

# Commit and push report-source changes back to GitHub.
# Requires .env.deploy with GITHUB_TOKEN and GITHUB_REPO.

if [[ -f .env.deploy ]]; then
  # shellcheck disable=SC1091
  source .env.deploy
fi

: "${GITHUB_REPO:=exkuretrol/familymart-5days-report}"
: "${GITHUB_TOKEN:?Set GITHUB_TOKEN}"

slug="${1:-}"
if [[ -z "$slug" ]]; then
  slug="$(TZ=Asia/Taipei date +%F)"
fi

# Pull latest source if this checkout already tracks the repo.
git config user.name "${GIT_AUTHOR_NAME:-exkuretrol}"
git config user.email "${GIT_AUTHOR_EMAIL:-33695301+exkuretrol@users.noreply.github.com}"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"
  git fetch origin main
  # Prefer current local changes if there is a same-file conflict; weekly jobs are authoritative for new report files.
  git pull --rebase --autostash origin main || git rebase --abort || true
fi

if git diff --quiet && git diff --cached --quiet; then
  echo "No Git changes to push"
else
  git add content package.json package-lock.json scripts wrangler.toml README.md .env.example .gitignore
  if git diff --cached --quiet; then
    echo "No report-source changes staged"
  else
    git commit -m "Add FamilyMart 5days report ${slug}"
    git push origin main
    echo "Pushed report source for ${slug}"
  fi
fi

# Avoid leaving token in repo config.
git remote set-url origin "git@github.com:${GITHUB_REPO}.git" || true
