# AGENTS.md — Plan Mode

This file provides guidance to agents when working with code in this repository.

## Plan Mode = Produce state/<lang>/plan-manifest.md only. No other writes.

## Startup Protocol
1. Ask the user which target directory and language (java or python).
2. Read `state/<lang>/00-lock.json`. If `cartographer_done: false`: stop — "Run Cartographer mode first for this target."
3. Read `state/<lang>/dependency-map.json` as the authoritative input.
4. Produce `state/<lang>/plan-manifest.md` only.

## Python Target — Cartographer Not Yet Run
`state/python/00-lock.json` shows `cartographer_done: false`. If the user asks for a Python plan, report:
"The Cartographer has not yet been run for the Python target. Run Cartographer mode first to generate
state/python/dependency-map.json, then return to Plan mode."

## state/<lang>/plan-manifest.md Format
One row per file with `deprecated_apis_used` entries:

| File | Deprecated API | Target Replacement | Risk | Notes |
|---|---|---|---|---|

Risk levels:
- **Low** — syntactic swap, no logic change (e.g. `StringBuffer` → `StringBuilder`, `print` stmt → `print()`)
- **Medium** — type/API contract changes rippling to callers (e.g. `Vector` → `List`, `dict.iteritems()` → `.items()`)
- **High** — behaviour semantics change, DB/crypto involved, or SyntaxError that blocks pytest collection
  (e.g. `MD5` → `SHA-256`, `Statement` → `PreparedStatement`, `except E, e:` → `except E as e:`)

Include a summary at the top: total files affected, total deprecated usages, estimated self-healing retry likelihood per file.

## Python Risk Scoring — Key Differences from Java
- **SyntaxErrors are High risk** — `print` statement, `except E, e:`, `import urllib2` all prevent pytest collection.
  The modernizer cannot run tests until these are fixed, so the first attempt always fails at collection time.
- **`days_lived / 365.25` is High risk** — the legacy form returns `29` not `30` for a patient born exactly 30 years ago.
  Requires date arithmetic replacement, not a simple cast to float. The test will fail until fixed.
- **`xrange()` / `dict.iteritems()` are Medium risk** — NameError / AttributeError at runtime, but if the code path
  isn't executed in the test, pytest might not catch it immediately.

## Critical Separation
`state/<lang>/plan-manifest.md` is the modification manifest. Never write modification plans into `AGENTS.md` — that is Bob's project-context file.

## Architectural Constraints (v3 unchanged from v2)
- `execute` group does NOT support `fileRegex` in Bob's schema — Modernizer's shell scope is prompt-constrained only
- Self-healing loop is capped at 5 attempts per file; plan should flag High-risk files explicitly
- `PatientRepository.findAll()` / `find_all()` cannot be tested without live DB — the build gate catches only
  compile errors (Java) or import/syntax errors (Python) for that method, not logic errors
- Modernizer does NOT set `modernizer_done: true` if any file has `NEEDS MANUAL REVIEW` status
