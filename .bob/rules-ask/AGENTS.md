# AGENTS.md — Ask Mode

This file provides guidance to agents when working with code in this repository.

## Ask Mode = Read-Only. Never writes anything.

## Startup Protocol
1. Ask which target: `java` or `python`
2. Read `state/<lang>/00-lock.json` — **always re-read, do not rely on hardcoded state below**
3. If `cartographer_done: false` (or file absent): report "Cartographer has not run yet for this target." Do not summarise absent data.
4. If `cartographer_done: true`: read `state/<lang>/dependency-map.json` and `state/<lang>/architecture-summary.md`

## Pipeline State (as of last commit — re-read lock files for current truth)
- **Java target (`state/java/`):** all 3 flags true; 7 state files present; PR #1 merged at https://github.com/TECXBOY/Chronos/pull/1
- **Python target (`state/python/`):** all flags false; only `00-lock.json` present; Cartographer has not yet run

## What Ask Mode Can Answer
- File inventory and dependency relationships from `state/<lang>/dependency-map.json`
- Current pipeline flag state from `state/<lang>/00-lock.json`
- Compliance findings from `state/<lang>/compliance-report.json`
- Questions about `REBUILD_BLUEPRINT.md`, `SPEC.md`, project structure
- Java vs Python target differences (seeded issues, deprecated APIs, test suite coverage)

## Non-Obvious Lookup Facts
- `architecture-summary.md` exists in `state/<lang>/` but is **not** fetched by dashboard JS — for human review only
- `outputs/` is v1 artifact storage — not read by current pipeline or dashboard
- `state/java/pr-body.md` (not `pr-draft.md`) is the real PR body used for `gh pr create --body-file`; `pr-draft.md` is the older human-readable summary
- Java compliance: 13 findings (11H/2M/0L); seeded issues span 6 files — all intentionally unfixed

## Authoritative References (priority order)
1. `REBUILD_BLUEPRINT.md §5` — v3 architecture (supersedes all earlier sections and SPEC.md pipeline description)
2. `SPEC.md §4` — compliance rule set (SEC-001, GDPR-032, GDPR-005, HIPAA-164, SEC-002) — language-agnostic, unchanged
3. `state/<lang>/00-lock.json` — current pipeline progress for the specified target
4. `PROJECT_BRIEF.md` — hackathon scope
