#!/usr/bin/env bash
# Restores global agent skills from skills/skill-lock.json.
# Installs each skill with the skills CLI, then links it into ~/.claude/skills.
# Safe to re-run. A failed skill prints a warning and does not stop the rest.
#
# Save the current state back into the repo with:
#   cp ~/.agents/.skill-lock.json skills/skill-lock.json
set -uo pipefail

LOCK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skill-lock.json"
SKILLS_HOME="${HOME}/.agents/skills"
CLAUDE_SKILLS="${HOME}/.claude/skills"

command -v jq >/dev/null 2>&1 || { echo "jq is required"; exit 1; }
command -v npx >/dev/null 2>&1 || { echo "npx is required"; exit 1; }
[ -f "$LOCK" ] || { echo "missing $LOCK"; exit 1; }

failed=()
while IFS=$'\t' read -r name url; do
  if [ -f "$SKILLS_HOME/$name/SKILL.md" ]; then
    echo "skip   $name (installed)"
    continue
  fi
  echo "add    $name from $url"
  if ! npx --yes skills add "$url" -g -s "$name" -a codex -y </dev/null; then
    echo "WARN   failed to install $name" >&2
    failed+=("$name")
  fi
done < <(jq -r '.skills | to_entries[] | select(.value.sourceType == "github") | [.key, .value.sourceUrl] | @tsv' "$LOCK")

mkdir -p "$CLAUDE_SKILLS"
for dir in "$SKILLS_HOME"/*/; do
  [ -d "$dir" ] || continue
  name="$(basename "$dir")"
  [ -e "$CLAUDE_SKILLS/$name" ] || ln -s "../../.agents/skills/$name" "$CLAUDE_SKILLS/$name"
done

if [ "${#failed[@]}" -gt 0 ]; then
  echo "Failed skills: ${failed[*]}" >&2
  exit 1
fi
echo "Skills restored."
