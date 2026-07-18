# AGENTS.md — Agent (Code) Mode

This file provides guidance to agents when working with code in this repository.

## Startup Gate — mandatory for every agent session
1. Ask user which target: `java` (`legacy-repo/`) or `python` (`legacy-repo-python/`)
2. Read `state/<lang>/00-lock.json` — **never skip**
   - Modernizer requires: `cartographer_done: true`
   - Compliance Officer requires: `modernizer_done: true`
   - If required flag is false: stop and report — do not proceed

## Write Boundaries (hard constraints)
- `cartographer`: writes only `state/(java|python)/(00-lock.json|dependency-map.json|architecture-summary.md)` — fileRegex enforced in schema
- `compliance-officer`: writes only `state/.*` — fileRegex enforced; physically cannot write to source directories
- `modernizer`: target source + `state/<lang>/(changelog.md|build-log.txt|00-lock.json|pr-body.md)` — prompt-constrained only (`execute` group has no fileRegex support in Bob's schema)

## Self-Healing Loop (Modernizer)
- Java gate: `mvn -q -f <target>/pom.xml test` | Python gate: `python3 -m pytest <target>/tests/ -q`
- Tool check first: `mvn -version` (Java) or `python3 -m pytest --version` (Python) — stop if not found
- Cap: 5 attempts per file; at cap append `NEEDS MANUAL REVIEW` to `state/<lang>/changelog.md`, do NOT set `modernizer_done: true`
- Never claim success without real exit code 0
- `modernizer_attempts[<file>]` resets to `0` on clean pass — Compliance Officer must not run until all files reset

## state/<lang>/changelog.md Format (dashboard parser is exact-match)
```
## <file path>
**Before:** ```<snippet>```
**After:** ```<snippet>```
**Reason:** <one line>
```
Manual-review fallback:
```
## <file path>
**STATUS: NEEDS MANUAL REVIEW**
Failed to pass test suite after 5 attempts. Final error in state/<lang>/build-log.txt.
```

## Python Target — Additional Constraints
- **TWO SyntaxErrors in `patient_repository.py`**: line 9 (`import urllib2`) AND line 50 (`except Exception, e:`) — both block pytest collection for `test_patient_repository.py` AND `test_notification_service.py`. Fix both before running gate.
- **Age calculation**: `days_lived / 365.25` → `today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))` — the test expects exactly `30`, not `29`.
- **`find_all()` untestable** — requires live DB. Don't attempt to test it; the gate only needs `hash_for_lookup()` tests to pass.
- **No mocks needed** — Python test stubs use anonymous subclasses, same pattern as Java.

## PR Automation Safety Rules (non-negotiable)
- `--draft` flag on `gh pr create`: **always, without exception**
- `repo_initialized` is **already `true`** in both lock files — **skip STEP A entirely**
- Never `git push origin main` (post-init is already complete)
- Never `git push --force`
- Never `gh pr merge` or `gh pr edit --ready-for-review`
- `git add` must be scoped to the target directory only (never `git add .` post-init)
- Show `git status --short` to user before every `git commit`
- If `gh pr create` exits non-zero: stop and report stderr — do NOT retry automatically

## Output File Reference (v3 — per-target state)
| File | Writer | Reader |
|---|---|---|
| `state/<lang>/00-lock.json` | All three agents + PR step | All three (startup gate) |
| `state/<lang>/dependency-map.json` | Cartographer | Modernizer, Compliance Officer, Dashboard |
| `state/<lang>/architecture-summary.md` | Cartographer | Human review only (not fetched by dashboard JS) |
| `state/<lang>/changelog.md` | Modernizer (append-only) | Dashboard Tab 2, PR body |
| `state/<lang>/build-log.txt` | Modernizer (overwrite per run) | Modernizer self-healing loop |
| `state/<lang>/compliance-report.json` | Compliance Officer | Dashboard Tab 3, PR body |
| `state/<lang>/pr-body.md` | Modernizer PR step (temp) | `gh pr create --body-file` |
| `state/<lang>/plan-manifest.md` | Plan mode | Modernizer work order |
