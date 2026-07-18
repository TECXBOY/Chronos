# AGENTS.md — Ask Mode

This file provides guidance to agents when working with code in this repository.

## Ask Mode = Read-Only State Summary. Never writes anything.

## Startup Protocol
1. Ask the user which target directory and language they want to query (java or python).
2. Read `state/<lang>/00-lock.json`.
3. If `cartographer_done: false` (or file absent): report "Cartographer has not run yet for this target." Do not summarise stale/absent data.
4. If `cartographer_done: true`: read `state/<lang>/dependency-map.json` and `state/<lang>/architecture-summary.md`.

## Current State
- **Java target:** `state/java/` fully populated (cartographer_done, modernizer_done, compliance_done all `true`).
  All 7 files present: 00-lock.json, dependency-map.json, architecture-summary.md, changelog.md, build-log.txt,
  compliance-report.json, pr-draft.md.
- **Python target:** `state/python/` has only `00-lock.json` (all flags `false`). Cartographer has not yet run
  for the Python target. No dependency-map.json, no compliance-report.json yet.

## What Ask Mode Can Answer
- File inventory and dependency relationships from `state/<lang>/dependency-map.json`
- Current pipeline flag state from `state/<lang>/00-lock.json`
- Compliance findings from `state/<lang>/compliance-report.json`
- Any questions about `REBUILD_BLUEPRINT.md`, `SPEC.md`, project structure
- Differences between Java and Python targets (seeded issues, deprecated APIs, test suite coverage)

## Authoritative References (priority order)
1. `REBUILD_BLUEPRINT.md` — supersedes SPEC.md for architecture/pipeline (now includes v3 multi-target changes)
2. `SPEC.md §4` — compliance rule set (SEC-001, GDPR-032, GDPR-005, HIPAA-164, SEC-002) — language-agnostic
3. `state/<lang>/00-lock.json` — current pipeline progress for the specified target
4. `PROJECT_BRIEF.md` — hackathon scope
