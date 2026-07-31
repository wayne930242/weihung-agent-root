#!/usr/bin/env bash
# Claude Code Status Line - Powerline blocks (left) + text (right)
# Intentionally omits `set -euo pipefail`: this runs on every render, and
# partial jq/git failures must not blank the statusline.
input=$(cat)

# Single jq pass, newline-separated
{
  IFS= read -r MODEL
  IFS= read -r CUR_DIR
  IFS= read -r PCT
  IFS= read -r RL_5H
  IFS= read -r RL_7D
  IFS= read -r LINES_ADDED
  IFS= read -r LINES_REMOVED
  IFS= read -r SESS_NAME
  IFS= read -r GIT_WT
  IFS= read -r AGENT
  IFS= read -r OUT_STYLE
} < <(echo "$input" | jq -r '
  .model.display_name // "?",
  .workspace.current_dir // "~",
  (.context_window.used_percentage // 0 | floor),
  (.rate_limits.five_hour.used_percentage // -1 | floor),
  (.rate_limits.seven_day.used_percentage // -1 | floor),
  (.cost.total_lines_added // 0),
  (.cost.total_lines_removed // 0),
  (.session_name // "" | gsub("\n"; " ")),
  (.workspace.git_worktree // ""),
  (.agent.name // ""),
  (.output_style.name // "default")
')

DIR_NAME="${CUR_DIR##*/}"

# Truncate session name to a 24-column visual width (fullwidth/CJK
# characters render as 2 columns, so this is ~12 CJK chars or 24 ASCII)
SESS_TRUNC=""
if [[ -n "$SESS_NAME" ]]; then
  SESS_TRUNC=$(SESS_NAME="$SESS_NAME" python3 -c '
import os, unicodedata
s = os.environ["SESS_NAME"]
w, out = 0, []
for c in s:
    cw = 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1
    if w + cw > 24:
        out.append("…")
        break
    out.append(c)
    w += cw
print("".join(out), end="")
')
fi

# Git info
BRANCH=""
STAGED=0
MODIFIED=0
if cd "$CUR_DIR" 2>/dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
  BRANCH=$(git branch --show-current 2>/dev/null)
  STAGED=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
  MODIFIED=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')
fi

# Context progress icon (single glyph, five stages)
if   [[ "$PCT" -lt 20 ]]; then ICON="○"
elif [[ "$PCT" -lt 40 ]]; then ICON="◔"
elif [[ "$PCT" -lt 60 ]]; then ICON="◑"
elif [[ "$PCT" -lt 80 ]]; then ICON="◕"
else                            ICON="●"
fi

# Compact-recommendation threshold (1M models compact earlier in absolute tokens)
case "$MODEL" in
  *1M*|*1m*) WARN_PCT=30 ;;  # 300K of 1M
  *)         WARN_PCT=70 ;;  # 140K of 200K
esac

# Threshold foreground color, scaled to WARN_PCT
ctx_fg() {
  local p=$1 w=$WARN_PCT
  local half=$((w / 2))
  local over=$((w * 13 / 10))
  if   [[ "$p" -lt "$half" ]]; then printf '\033[38;5;82m'   # green
  elif [[ "$p" -lt "$w" ]];    then printf '\033[38;5;226m'  # yellow
  elif [[ "$p" -lt "$over" ]]; then printf '\033[38;5;208m'  # orange
  else                              printf '\033[38;5;196m'  # red
  fi
}

# Rate-limit color (fixed thresholds)
pct_fg() {
  local p=$1
  if   [[ "$p" -lt 50 ]]; then printf '\033[38;5;82m'
  elif [[ "$p" -lt 70 ]]; then printf '\033[38;5;226m'
  elif [[ "$p" -lt 90 ]]; then printf '\033[38;5;208m'
  else                         printf '\033[38;5;196m'
  fi
}

R=$'\033[0m'
GRAY=$'\033[38;5;244m'
DIM=$'\033[2m'

# LEFT: powerline-style BG blocks (cyberpunk palette)
L_MODEL=$(printf '\033[48;5;198m\033[38;5;255m\033[1m  %s %s'   "$MODEL"    "$R")
L_DIR=$(printf   '\033[48;5;23m\033[38;5;255m  %s %s'           "$DIR_NAME" "$R")

L_BRANCH=""
if [[ -n "$BRANCH" ]]; then
  GIT_BODY="$BRANCH"
  [[ "$STAGED"   -gt 0 ]] && GIT_BODY="$GIT_BODY +$STAGED"
  [[ "$MODIFIED" -gt 0 ]] && GIT_BODY="$GIT_BODY ~$MODIFIED"
  L_BRANCH=$(printf '\033[48;5;54m\033[38;5;255m  %s %s' "$GIT_BODY" "$R")
fi

L_SESS=""
[[ -n "$SESS_TRUNC" ]] && L_SESS=$(printf '\033[48;5;238m\033[38;5;255m  %s %s' "$SESS_TRUNC" "$R")

L_WT=""
[[ -n "$GIT_WT" ]] && L_WT=$(printf '\033[48;5;25m\033[38;5;255m  %s %s' "$GIT_WT" "$R")

L_AG=""
[[ -n "$AGENT" ]] && L_AG=$(printf '\033[48;5;130m\033[38;5;255m  %s %s' "$AGENT" "$R")

L_OS=""
[[ "$OUT_STYLE" != "default" && -n "$OUT_STYLE" ]] \
  && L_OS=$(printf ' %s %s%s' "$DIM" "$OUT_STYLE" "$R")

LEFT="${L_MODEL}${L_DIR}${L_SESS}${L_BRANCH}${L_WT}${L_AG}${L_OS}"

# RIGHT: plain text with icon + threshold colors
CTX_C=$(ctx_fg "$PCT")
WARN=""
[[ "$PCT" -ge "$WARN_PCT" ]] && WARN=" ⚠"
R_CTX=$(printf '%s%s %s%%%s%s' "$CTX_C" "$ICON" "$PCT" "$WARN" "$R")

R_RL=""
if [[ "$RL_5H" -ge 0 && "$RL_7D" -ge 0 ]]; then
  RL5_C=$(pct_fg "$RL_5H")
  RL7_C=$(pct_fg "$RL_7D")
  R_RL=$(printf '   %s⏳ %s%s%%%s/%s%s%%%s' "$GRAY" "$RL5_C" "$RL_5H" "$R" "$RL7_C" "$RL_7D" "$R")
elif [[ "$RL_5H" -ge 0 ]]; then
  RL5_C=$(pct_fg "$RL_5H")
  R_RL=$(printf '   %s⏳ %s%s%%%s' "$GRAY" "$RL5_C" "$RL_5H" "$R")
elif [[ "$RL_7D" -ge 0 ]]; then
  RL7_C=$(pct_fg "$RL_7D")
  R_RL=$(printf '   %s⏳ %s%s%%%s' "$GRAY" "$RL7_C" "$RL_7D" "$R")
fi

R_DIFF=""
if [[ "$LINES_ADDED" -gt 0 || "$LINES_REMOVED" -gt 0 ]]; then
  R_DIFF=$(printf '   \033[38;5;82m+%s%s \033[38;5;196m-%s%s' "$LINES_ADDED" "$R" "$LINES_REMOVED" "$R")
fi

RIGHT="${R_CTX}${R_RL}${R_DIFF}"

# Fixed gap, not width-computed alignment: the row's true render width
# isn't reliably measurable from here.
printf '%s   %s\n' "$LEFT" "$RIGHT"
