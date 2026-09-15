#!/bin/bash
# Publish the site: render everything, commit all changes, push.
# Usage: ./publish.sh "commit message"
set -e
cd "$(dirname "$0")"

MSG="${1:-update site}"

quarto render
git add -A
if git diff --cached --quiet; then
  echo "Nothing to commit — site already up to date."
  exit 0
fi
git commit -m "$MSG"
git push
echo "Done. Netlify will deploy the new version shortly."
