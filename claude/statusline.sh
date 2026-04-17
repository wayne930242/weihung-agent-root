#!/usr/bin/env bash
# Claude Code Status Line - Powerline blocks (left) + text (right), aligned
# Intentionally omits `set -euo pipefail`: this runs on every render, and
# partial jq/git/tput failures must not blank the statusline.
input=$(cat)

# Single jq pass, newline-separated
{
  IFS= read -r MODEL
  IFS= read -r CUR_DIR
  IFS= read -r PCT
  IFS= read -r COST
  IFS= read -r DUR_MS
  IFS= read -r RL_5H
  IFS= read -r GIT_WT
  IFS= read -r AGENT
  IFS= read -r OUT_STYLE
} < <(echo "$input" | jq -r '
  .model.display_name // "?",
  .workspace.current_dir // "~",
  (.context_window.used_percentage // 0 | floor),
  (.cost.total_cost_usd // 0),
  (.cost.total_duration_ms // 0),
  (.rate_limits.five_hour.used_percentage // -1 | floor),
  (.workspace.git_worktree // ""),
  (.agent.name // ""),
  (.output_style.name // "default")
')

DIR_NAME="${CUR_DIR##*/}"

# Git info
BRANCH=""
STAGED=0
MODIFIED=0
if cd "$CUR_DIR" 2>/dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
  BRANCH=$(git branch --show-current 2>/dev/null)
  STAGED=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
  MODIFIED=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')
fi

# Cost / duration
COST_FMT=$(printf '%.2f' "$COST")
DUR_S=$((DUR_MS / 1000))
DUR_M=$((DUR_S / 60))
DUR_H=$((DUR_M / 60))
if   [[ "$DUR_H" -gt 0 ]]; then DUR="${DUR_H}h$((DUR_M % 60))m"
elif [[ "$DUR_M" -gt 0 ]]; then DUR="${DUR_M}m"
else                            DUR="${DUR_S}s"
fi

# Context progress bar (6 wide)
BAR_W=6
FILLED=$((PCT * BAR_W / 100))
[[ "$FILLED" -gt "$BAR_W" ]] && FILLED=$BAR_W
EMPTY=$((BAR_W - FILLED))
BAR=""
[[ "$FILLED" -gt 0 ]] && printf -v F_STR "%${FILLED}s" "" && BAR="${F_STR// /▰}"
[[ "$EMPTY"  -gt 0 ]] && printf -v E_STR "%${EMPTY}s"  "" && BAR="${BAR}${E_STR// /▱}"

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

L_WT=""
[[ -n "$GIT_WT" ]] && L_WT=$(printf '\033[48;5;25m\033[38;5;255m  %s %s' "$GIT_WT" "$R")

L_AG=""
[[ -n "$AGENT" ]] && L_AG=$(printf '\033[48;5;130m\033[38;5;255m  %s %s' "$AGENT" "$R")

L_OS=""
[[ "$OUT_STYLE" != "default" && -n "$OUT_STYLE" ]] \
  && L_OS=$(printf ' %s %s%s' "$DIM" "$OUT_STYLE" "$R")

LEFT="${L_MODEL}${L_DIR}${L_BRANCH}${L_WT}${L_AG}${L_OS}"

# RIGHT: plain text with icon + threshold colors
CTX_C=$(ctx_fg "$PCT")
WARN=""
[[ "$PCT" -ge "$WARN_PCT" ]] && WARN=" ⚠"
R_CTX=$(printf  '%sctx %s %s%%%s%s' "$CTX_C" "$BAR"      "$PCT"      "$WARN" "$R")
R_COST=$(printf '%s $%s%s'          "$GRAY"  "$COST_FMT" "$R")
R_DUR=$(printf  '%s %s%s'           "$GRAY"  "$DUR"      "$R")

R_RL=""
if [[ "$RL_5H" -ge 0 ]]; then
  RL_C=$(pct_fg "$RL_5H")
  R_RL=$(printf '   %s5h %s%%%s' "$RL_C" "$RL_5H" "$R")
fi

RIGHT="${R_CTX}   ${R_COST}   ${R_DUR}${R_RL}"

# Terminal width (fallback 120 if no tty)
COLS=$(tput cols 2>/dev/null || echo 120)

# Compose with left/right alignment (Python handles unicode width)
LEFT="$LEFT" RIGHT="$RIGHT" COLS="$COLS" python3 - <<'PYEOF'
import os, re, sys, unicodedata
left  = os.environ['LEFT']
right = os.environ['RIGHT']
cols  = int(os.environ['COLS'])

ansi = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]')

def visual_width(s):
    s = ansi.sub('', s)
    total = 0
    for c in s:
        cp = ord(c)
        # Nerd Font Private Use Areas rendered width-2 in most terminals
        if 0xE000 <= cp <= 0xF8FF or 0xF0000 <= cp <= 0xFFFFD:
            total += 2
        elif unicodedata.east_asian_width(c) in ('W', 'F'):
            total += 2
        elif unicodedata.combining(c):
            total += 0
        else:
            total += 1
    return total

lw = visual_width(left)
rw = visual_width(right)
pad = max(2, cols - lw - rw)
sys.stdout.write(left + ' ' * pad + right + '\n')
PYEOF
