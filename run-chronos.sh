#!/usr/bin/env bash
# =============================================================================
# run-chronos.sh — Chronos pipeline orchestration wrapper
#
# Usage:
#   ./run-chronos.sh <target-dir> <language>
#   ./run-chronos.sh --help
#
# Arguments:
#   target-dir   Path to the legacy codebase to process
#                (e.g. legacy-repo/ or legacy-repo-python/)
#   language     One of: java, python
#
# What this script does:
#   1. Validates arguments and required tools
#   2. Prints step-by-step instructions for running each Bob mode in sequence
#   3. Polls state/<language>/00-lock.json after each step (10-min timeout)
#   4. Verifies each flag before proceeding to the next stage
#   5. Prints a final summary: finding counts by severity, change count,
#      output file paths, and PR URL if available
#
# Note on Bob IDE:
#   Bob is a desktop IDE (not a headless CLI tool). This script cannot invoke
#   Bob automatically. Instead it guides you through the three modes interactively,
#   polling the shared state directory to detect when each stage completes.
#
# Requirements:
#   - bash 3.2+
#   - jq   (for parsing state/<lang>/00-lock.json and compliance-report.json)
#   - python3 or gawk (for awk-based markdown counting fallback)
# =============================================================================

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; AMBER='\033[0;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────────────
info()    { printf "${CYAN}[chronos]${RESET} %s\n" "$*"; }
success() { printf "${GREEN}[chronos]${RESET} %s\n" "$*"; }
warn()    { printf "${AMBER}[chronos]${RESET} %s\n" "$*"; }
fail()    { printf "${RED}[chronos] ERROR:${RESET} %s\n" "$*" >&2; exit 1; }
divider() { printf "${CYAN}%s${RESET}\n" "────────────────────────────────────────────────────────────"; }

usage() {
  cat <<EOF

${BOLD}USAGE${RESET}
  ./run-chronos.sh <target-dir> <language>

${BOLD}ARGUMENTS${RESET}
  target-dir   Directory containing the legacy codebase
               Examples: legacy-repo/  or  legacy-repo-python/
  language     Target language — must be exactly: java  or  python

${BOLD}EXAMPLES${RESET}
  ./run-chronos.sh legacy-repo java
  ./run-chronos.sh legacy-repo-python python

${BOLD}WHAT IT DOES${RESET}
  Guides you through the three Chronos Bob modes in sequence:
    1/3  Cartographer  — static analysis → state/<lang>/dependency-map.json
    2/3  Modernizer    — refactor + self-healing loop + draft PR
    3/3  Compliance Officer — audit → state/<lang>/compliance-report.json

  After each mode, polls state/<lang>/00-lock.json (10-min timeout) until
  the relevant flag is set to true, then prints a summary.

${BOLD}REQUIREMENTS${RESET}
  - jq must be installed (brew install jq  or  apt install jq)
  - Bob IDE open with this workspace loaded

EOF
  exit 0
}

# ── Argument handling ─────────────────────────────────────────────────────────
[[ "${1:-}" == "--help" || "${1:-}" == "-h" ]] && usage
[[ $# -ne 2 ]] && { usage; }

TARGET_DIR="$1"
LANG="$2"

# Validate language
if [[ "$LANG" != "java" && "$LANG" != "python" ]]; then
  fail "language must be 'java' or 'python', got: '$LANG'"
fi

# Validate target directory exists
[[ -d "$TARGET_DIR" ]] || fail "target directory not found: '$TARGET_DIR'"

# ── Tool checks ───────────────────────────────────────────────────────────────
if ! command -v jq &>/dev/null; then
  fail "jq is required but not found on PATH. Install with: brew install jq"
fi

# Language-specific build tool check
if [[ "$LANG" == "java" ]]; then
  command -v mvn &>/dev/null || fail "mvn is required for Java target but not found on PATH"
  BUILD_GATE="mvn -q -f ${TARGET_DIR}/pom.xml test"
  BUILD_TOOL="mvn"
else
  command -v python3 &>/dev/null || fail "python3 is required for Python target but not found on PATH"
  python3 -m pytest --version &>/dev/null || fail "pytest is required but not installed. Run: pip install pytest"
  BUILD_GATE="python3 -m pytest ${TARGET_DIR}/tests/ -q"
  BUILD_TOOL="pytest"
fi

STATE_DIR="state/${LANG}"
LOCK_FILE="${STATE_DIR}/00-lock.json"
TIMEOUT_SECS=600   # 10 minutes per stage
POLL_INTERVAL=10   # check every 10 seconds

# Ensure state directory exists
mkdir -p "$STATE_DIR"

# ── Lock file initialisation ──────────────────────────────────────────────────
if [[ ! -f "$LOCK_FILE" ]]; then
  warn "Lock file not found — creating: $LOCK_FILE"
  cat > "$LOCK_FILE" <<JSON
{
  "cartographer_done": false,
  "modernizer_done": false,
  "compliance_done": false,
  "modernizer_attempts": {},
  "last_updated": null,
  "repo_initialized": false,
  "repo_remote": "https://github.com/TECXBOY/Chronos.git",
  "pages_url": "https://tecxboy.github.io/Chronos/",
  "pr_url": null
}
JSON
fi

# ── Poll helper ───────────────────────────────────────────────────────────────
# poll_flag <flag_name> <stage_label>
# Blocks until .flag == true in LOCK_FILE or timeout; exits non-zero on timeout.
poll_flag() {
  local flag="$1"
  local label="$2"
  local elapsed=0

  info "Waiting for ${flag} = true in ${LOCK_FILE} ..."
  while true; do
    local val
    val=$(jq -r ".${flag}" "$LOCK_FILE" 2>/dev/null || echo "false")
    if [[ "$val" == "true" ]]; then
      return 0
    fi
    if (( elapsed >= TIMEOUT_SECS )); then
      fail "Timeout after ${TIMEOUT_SECS}s waiting for ${flag}. Check Bob for errors.\n  Lock file: ${LOCK_FILE}"
    fi
    printf "  ${AMBER}·${RESET} ${label} not complete yet (${elapsed}s elapsed) — checking again in ${POLL_INTERVAL}s ...\n"
    sleep "$POLL_INTERVAL"
    elapsed=$(( elapsed + POLL_INTERVAL ))
  done
}

# ── Stage runner ──────────────────────────────────────────────────────────────
run_stage() {
  local step="$1"       # e.g. "1/3"
  local mode="$2"       # e.g. "cartographer"
  local flag="$3"       # e.g. "cartographer_done"
  local desc="$4"       # human description

  divider
  local mode_upper
  mode_upper=$(echo "$mode" | tr '[:lower:]' '[:upper:]')
  printf "\n${BOLD}[${step}] ${mode_upper}${RESET}  —  ${desc}\n\n"

  # Check if already done
  local current_val
  current_val=$(jq -r ".${flag}" "$LOCK_FILE" 2>/dev/null || echo "false")
  if [[ "$current_val" == "true" ]]; then
    success "${flag} is already true — skipping this stage."
    return 0
  fi

  # Print Bob instructions
  cat <<INSTRUCTIONS
${CYAN}  ➜  In Bob IDE:${RESET}
     1. Switch to the '${BOLD}${mode}${RESET}' custom mode
     2. Send this prompt (copy/paste):

        ${BOLD}Scan ${TARGET_DIR}/ for the ${LANG} target.
        Use state/${LANG}/ as the state directory.${RESET}

     3. Wait for Bob to complete and write ${LOCK_FILE}
     4. Return here — this script will detect completion automatically.

INSTRUCTIONS

  poll_flag "$flag" "$mode"
  success "${step} ${mode} complete ✓"
  printf "\n"
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
divider
printf "\n${BOLD}  CHRONOS PIPELINE${RESET}  ·  target: ${BOLD}${TARGET_DIR}${RESET}  ·  lang: ${BOLD}${LANG}${RESET}\n\n"
info "State directory : ${STATE_DIR}/"
info "Lock file       : ${LOCK_FILE}"
info "Build gate      : ${BUILD_GATE}"
info "Timeout per stage: ${TIMEOUT_SECS}s"
printf "\n"

# ── [1/3] Cartographer ────────────────────────────────────────────────────────
run_stage "1/3" "cartographer" "cartographer_done" \
  "static analysis → dependency-map.json + architecture-summary.md"

# ── [2/3] Modernizer ──────────────────────────────────────────────────────────
run_stage "2/3" "modernizer" "modernizer_done" \
  "refactor + self-healing build loop (gate: ${BUILD_TOOL}) + draft PR"

# ── [3/3] Compliance Officer ──────────────────────────────────────────────────
run_stage "3/3" "compliance-officer" "compliance_done" \
  "security + GDPR/HIPAA audit → compliance-report.json"

# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
divider
printf "\n${BOLD}  PIPELINE COMPLETE — SUMMARY${RESET}\n\n"

# Compliance counts
if [[ -f "${STATE_DIR}/compliance-report.json" ]]; then
  HIGH=$(jq -r '.summary.high   // 0' "${STATE_DIR}/compliance-report.json")
  MED=$(jq  -r '.summary.medium // 0' "${STATE_DIR}/compliance-report.json")
  LOW=$(jq  -r '.summary.low    // 0' "${STATE_DIR}/compliance-report.json")
  TOTAL_FINDINGS=$(( HIGH + MED + LOW ))
  printf "  Compliance findings : ${RED}${HIGH} High${RESET}  ${AMBER}${MED} Medium${RESET}  ${GREEN}${LOW} Low${RESET}  (${TOTAL_FINDINGS} total)\n"
else
  warn "compliance-report.json not found — compliance summary unavailable"
fi

# Change count from changelog.md
if [[ -f "${STATE_DIR}/changelog.md" ]]; then
  CHANGE_COUNT=$(grep -c '^## ' "${STATE_DIR}/changelog.md" 2>/dev/null || echo "0")
  printf "  Modernization changes: ${BOLD}${CHANGE_COUNT}${RESET}\n"
else
  warn "changelog.md not found — change count unavailable"
fi

# PR URL
PR_URL=$(jq -r '.pr_url // empty' "$LOCK_FILE" 2>/dev/null || true)
if [[ -n "$PR_URL" ]]; then
  printf "  Draft PR            : ${CYAN}${PR_URL}${RESET}\n"
else
  warn "No PR URL in lock file — PR may not have been created yet"
fi

# Output file paths
printf "\n  Output files:\n"
for f in dependency-map.json architecture-summary.md changelog.md build-log.txt compliance-report.json pr-body.md; do
  path="${STATE_DIR}/${f}"
  if [[ -f "$path" ]]; then
    printf "    ${GREEN}✓${RESET}  ${path}\n"
  else
    printf "    ${AMBER}–${RESET}  ${path}  (not present)\n"
  fi
done

printf "\n"
divider
success "All three stages complete for '${LANG}' target.  Dashboard: https://tecxboy.github.io/Chronos/"
printf "\n"
