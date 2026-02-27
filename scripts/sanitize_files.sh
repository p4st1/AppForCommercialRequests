#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

sanitized_count=0

while IFS= read -r -d '' file; do
  encoding="$(file -b --mime-encoding "$file" 2>/dev/null || true)"
  if [[ "$encoding" == "utf-16" || "$encoding" == "utf-16le" || "$encoding" == "utf-16be" ]]; then
    tmp_file="$(mktemp)"
    if iconv -c -f "$encoding" -t "utf-8" "$file" > "$tmp_file" 2>/dev/null; then
      mv "$tmp_file" "$file"
    else
      rm -f "$tmp_file"
      continue
    fi
  fi

  perl -i -pe 's/^\xEF\xBB\xBF//' "$file"
  perl -i -pe 's/\r$//' "$file"
  perl -i -pe 's/[ \t]+$//' "$file"

  if [[ -s "$file" ]] && [[ "$(tail -c 1 "$file" | wc -l | tr -d '[:space:]')" == "0" ]]; then
    printf '\n' >> "$file"
  fi

  sanitized_count=$((sanitized_count + 1))
done < <(
  rg --files -0 \
    -g '*.py' \
    -g '*.md' \
    -g '*.txt' \
    -g '*.json' \
    -g '*.ui' \
    -g '*.yml' \
    -g '*.yaml' \
    -g '*.toml' \
    -g '*.ini' \
    -g '*.cfg' \
    -g '*.spec' \
    -g '.gitignore' \
    -g '.gitattributes' \
    -g '!venv/**' \
    -g '!build/**' \
    -g '!dist/**' \
    -g '!__pycache__/**' \
    -g '!.git/**'
)

printf 'Sanitized %d files.\n' "$sanitized_count"
