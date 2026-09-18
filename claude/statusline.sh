#!/usr/bin/env bash
# Claude Code Status Line - model/dir/usage, git, and session/context rows, fitted to COLUMNS
# Intentionally omits `set -euo pipefail`: this runs on every render, and
# partial jq/git failures must not blank the statusline.
input=$(cat)

# Single jq pass, newline-separated. Without jq there is nothing to parse,
# so fall back to inert values and still render the git/dir half of the row.
if command -v jq > /dev/null 2>&1; then
  {
    IFS= read -r MODEL
    IFS= read -r CUR_DIR
    IFS= read -r PCT
    IFS= read -r RL_5H
    IFS= read -r RL_7D
    IFS= read -r LINES_ADDED
    IFS= read -r LINES_REMOVED
    IFS= read -r GIT_WT
    IFS= read -r AGENT
    IFS= read -r SESS_NAME
    IFS= read -r OUT_STYLE
  } < <(echo "$input" | jq -r '
    .model.display_name // "?",
    .workspace.current_dir // "~",
    (.context_window.used_percentage // 0 | floor),
    (.rate_limits.five_hour.used_percentage // -1 | floor),
    (.rate_limits.seven_day.used_percentage // -1 | floor),
    (.cost.total_lines_added // 0),
    (.cost.total_lines_removed // 0),
    (.workspace.git_worktree // ""),
    (.agent.name // ""),
    (.session_name // "" | gsub("\n"; " ")),
    (.output_style.name // "default")
  ')
else
  MODEL="jq missing"
  CUR_DIR="$PWD"
  PCT=0
  RL_5H=-1
  RL_7D=-1
  LINES_ADDED=0
  LINES_REMOVED=0
  GIT_WT=""
  AGENT=""
  SESS_NAME=""
  OUT_STYLE="default"
fi

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

# Context progress icon: an empty circle, then one slice per 12.5% used
CTX_ICONS=(󰝦 󰪞 󰪟 󰪠 󰪡 󰪢 󰪣 󰪤 󰪥)
CTX_STEP=$(( (PCT * 8 + 99) / 100 ))
(( CTX_STEP > 8 )) && CTX_STEP=8
ICON=${CTX_ICONS[CTX_STEP]}

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

# Shortest model label: "Opus 5 (1M context)" -> "O5[1m]", "Haiku 4.5" -> "H4.5"
MODEL_SHORT="$MODEL"
if [[ "$MODEL" =~ ^([A-Za-z])[A-Za-z]*\ ([0-9][0-9.]*) ]]; then
  MODEL_SHORT="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
  [[ "$MODEL" == *1[Mm]* ]] && MODEL_SHORT="${MODEL_SHORT}[1m]"
fi

# Segments: a Nerd Font icon and text in the segment's foreground color
L_MODEL=$(printf '\033[1;38;5;198m %s%s' "$MODEL_SHORT" "$R")
L_DIR=$(printf   '\033[38;5;37m󰉋 %s%s'     "$DIR_NAME"    "$R")

GIT_COUNTS=""
[[ "$STAGED"   -gt 0 ]] && GIT_COUNTS="$GIT_COUNTS +$STAGED"
[[ "$MODIFIED" -gt 0 ]] && GIT_COUNTS="$GIT_COUNTS ~$MODIFIED"
branch_seg() {
  L_BRANCH=""
  [[ -n "$1" ]] && printf -v L_BRANCH '\033[38;5;141m %s%s%s' "$1" "$GIT_COUNTS" "$R"
}
branch_seg "$BRANCH"

sess_seg() {
  L_SESS=""
  [[ -n "$1" ]] && printf -v L_SESS '\033[38;5;252m󰚩 %s%s' "$1" "$R"
}
sess_seg "$SESS_NAME"

L_WT=""
[[ -n "$GIT_WT" ]] && L_WT=$(printf '\033[38;5;75m󰙅 %s%s' "$GIT_WT" "$R")

L_AG=""
[[ -n "$AGENT" ]] && L_AG=$(printf '\033[38;5;173m󱍰 %s%s' "$AGENT" "$R")

L_OS=""
[[ "$OUT_STYLE" != "default" && -n "$OUT_STYLE" ]] \
  && L_OS=$(printf '%s󰸌 %s%s' "$DIM" "$OUT_STYLE" "$R")

# Context and rate limits color their numbers by threshold
CTX_C=$(ctx_fg "$PCT")
WARN=""
[[ "$PCT" -ge "$WARN_PCT" ]] && WARN=" 󰀦"
R_CTX=$(printf '%s%s %s%%%s%s' "$CTX_C" "$ICON" "$PCT" "$WARN" "$R")

R_RL=""
if [[ "$RL_5H" -ge 0 && "$RL_7D" -ge 0 ]]; then
  RL5_C=$(pct_fg "$RL_5H")
  RL7_C=$(pct_fg "$RL_7D")
  R_RL=$(printf '%s󰔟 %s%s%%%s/%s%s%%%s' "$GRAY" "$RL5_C" "$RL_5H" "$R" "$RL7_C" "$RL_7D" "$R")
elif [[ "$RL_5H" -ge 0 ]]; then
  RL5_C=$(pct_fg "$RL_5H")
  R_RL=$(printf '%s󰔟 %s%s%%%s' "$GRAY" "$RL5_C" "$RL_5H" "$R")
elif [[ "$RL_7D" -ge 0 ]]; then
  RL7_C=$(pct_fg "$RL_7D")
  R_RL=$(printf '%s󰔟 %s%s%%%s' "$GRAY" "$RL7_C" "$RL_7D" "$R")
fi

R_DIFF=""
if [[ "$LINES_ADDED" -gt 0 || "$LINES_REMOVED" -gt 0 ]]; then
  R_DIFF=$(printf '\033[38;5;82m+%s%s \033[38;5;196m-%s%s' "$LINES_ADDED" "$R" "$LINES_REMOVED" "$R")
fi

# Column width of one character: wide East Asian and emoji take two.
char_width() {
  local cp
  printf -v cp '%d' "'$1"
  if (( (cp >= 0x1100 && cp <= 0x115F)
     || (cp >= 0x2E80 && cp <= 0xA4CF) || (cp >= 0xAC00 && cp <= 0xD7A3)
     || (cp >= 0xF900 && cp <= 0xFAFF) || (cp >= 0xFE30 && cp <= 0xFE4F)
     || (cp >= 0xFF00 && cp <= 0xFF60) || (cp >= 0xFFE0 && cp <= 0xFFE6)
     || (cp >= 0x1F300 && cp <= 0x1FAFF) || (cp >= 0x20000 && cp <= 0x3FFFD) )); then
    CW=2
  else
    CW=1
  fi
}

# Visible width into VW: strip SGR escapes, count characters, then add the
# extra column of each wide one (only non-ASCII characters can be wide).
shopt -s extglob
vis_width() {
  local s=${1//$'\033['*([0-9;])m/} wide i
  VW=${#s}
  wide=${s//[ -~]/}
  for ((i = 0; i < ${#wide}; i++)); do
    char_width "${wide:i:1}"
    VW=$((VW + CW - 1))
  done
}

# Cut a plain string into TRUNC to fit a column budget, marking the cut with …
truncate_cols() {
  local s=$1 budget=$2 i w=0
  TRUNC=$s
  vis_width "$s"
  (( VW <= budget )) && return
  TRUNC=""
  for ((i = 0; i < ${#s}; i++)); do
    char_width "${s:i:1}"
    (( w + CW > budget - 1 )) && break
    TRUNC+=${s:i:1}
    w=$((w + CW))
  done
  TRUNC+="…"
}

# Claude Code sets COLUMNS to the pane width before each render; the
# reserve covers its built-in row spacing.
MAX=""
[[ -n "$COLUMNS" ]] && MAX=$((COLUMNS - 4))
fits() {
  [[ -z "$MAX" ]] && return 0
  vis_width "$1"
  (( VW <= MAX ))
}

# Shorten a row's name segment to the columns the row has left; MIN_NAME is
# the shortest cut worth keeping.
MIN_NAME=6
fit_name() {  # <name> <segment-setter> <row-fn> <row-var>
  local name=$1 set_seg=$2 row_fn=$3 row_var=$4 room
  "$set_seg" "x"
  "$row_fn"
  vis_width "${!row_var}"
  room=$((MAX - VW + 1))
  if (( room >= MIN_NAME )); then
    truncate_cols "$name" "$room"
    "$set_seg" "$TRUNC"
  else
    "$set_seg" ""
  fi
  "$row_fn"
}

# Join a row's non-empty segments with a two-column gap.
join_row() {  # <row-var> <segment>...
  local var=$1 out="" seg
  shift
  for seg in "$@"; do
    [[ -n "$seg" ]] && out+="${out:+  }$seg"
  done
  printf -v "$var" '%s' "$out"
}

# Each row drops its optional segments, lowest priority first, until it fits.
row1() { join_row ROW1 "$L_MODEL" "$L_DIR" "$R_RL"; }
row1
fits "$ROW1" || { R_RL="";  row1; }
fits "$ROW1" || { L_DIR=""; row1; }

row2() { join_row ROW2 "$L_BRANCH" "$R_DIFF" "$L_WT"; }
row2
fits "$ROW2" || { R_DIFF=""; row2; }
fits "$ROW2" || { L_WT="";   row2; }
fits "$ROW2" || fit_name "$BRANCH" branch_seg row2 ROW2

row3() { join_row ROW3 "$L_SESS" "$L_AG" "$R_CTX" "$L_OS"; }
row3
fits "$ROW3" || { L_OS=""; row3; }
fits "$ROW3" || { L_AG=""; row3; }
fits "$ROW3" || fit_name "$SESS_NAME" sess_seg row3 ROW3

printf '%s\n' "$ROW1"
if [[ -n "$ROW2" ]]; then
  printf '%s\n' "$ROW2"
fi
printf '%s\n' "$ROW3"
