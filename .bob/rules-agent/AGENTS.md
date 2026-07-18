# AGENTS.md — Agent (Code) Mode

This file provides guidance to agents when working with code in this repository.

## Startup Gate — mandatory for every agent session
Read `state/<lang>/00-lock.json` first (user must specify lang: java or python). Never skip.
- Modernizer requires: `cartographer_done: true`
- Compliance Officer requires: `modernizer_done: true`
- If the required flag is false: stop and report — do not proceed.

## Write Boundaries (hard constraints, unchanged from v2)
- `cartographer`: only `state/(java|python)/(00-lock.json|dependency-map.json|architecture-summary.md)` — fileRegex enforced
- `compliance-officer`: only `state/.*` — fileRegex enforced; physically cannot write to target repos
- `modernizer`: target source + `state/<lang>/changelog.md`, `state/<lang>/build-log.txt`, `state/<lang>/00-lock.json` — prompt-constrained only (`execute` group has no fileRegex support)

## Self-Healing Loop (Modernizer — v3 adds language detection)
- Gate command is language-dependent: `mvn -q -f <target>/pom.xml test` (Java) or `python3 -m pytest <target>/tests/ -q` (Python)
- Tool check: `mvn -version` (Java) or `python3 -m pytest --version` (Python) before loop; stop if not found
- Cap: 5 attempts per file; at cap append `NEEDS MANUAL REVIEW` to `state/<lang>/changelog.md`, do NOT set `modernizer_done: true`
- Never claim success without a real passing exit 0
- `modernizer_attempts[<file>]` resets to `0` on a clean pass; Compliance Officer must not run until all files reset (no `NEEDS MANUAL REVIEW` entries)

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
- Legacy `.py` files have Python 2 **SyntaxErrors** in Python 3 (print statement, except E, e:, import urllib2)
  — pytest will fail at collection time before modernization, which is correct. The Modernizer must fix
  syntax errors before pytest can collect tests.
- `patient_repository.py` has TWO SyntaxErrors (line 9: `import urllib2`; line 50: `except Exception, e:`).
  Both must be fixed, or the file is unparseable and pytest cannot import `PatientRepository`.
- Age calculation uses `days_lived / 365.25` → returns `29` for a patient born exactly 30 years ago.
  Test expects `30`. Must replace with `today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))`.
- `PatientRepository.find_all()` cannot be tested without a live DB (same constraint as Java).

## Agent Mode Full Pipeline (v3 with PR automation)
1. User specifies target directory and language (java or python)
2. Read `state/<lang>/plan-manifest.md` as the Modernizer work order (produced by Plan mode)
3. Run Modernizer self-healing loop per file in `state/<lang>/dependency-map.json`
4. If `modernizer_done: true`, run Compliance Officer audit → `compliance_done: true`
5. **PR AUTOMATION** (all three flags true):
   - One-time init if `repo_initialized: false`: `git remote add`, `git add .`, `git commit`, `git push -u origin main` → sets `repo_initialized: true` in BOTH lock files
   - `git checkout -b chronos/modernize-<lang>-<timestamp>`
   - `git add <target-dir>/ state/<lang>/` → `git status --short` (show staged files before commit)
   - `git commit -m "feat(chronos-<lang>): ..."` (message built from real changelog + compliance counts)
   - `git push origin <branch>`
   - Write `state/<lang>/pr-body.md` from real changelog + compliance table
   - `gh pr create --draft --base main --head <branch> --body-file state/<lang>/pr-body.md`
   - Write returned URL to `state/<lang>/00-lock.json` as `pr_url`

## PR Automation Safety Rules (non-negotiable)
- `--draft` flag on `gh pr create`: **always, without exception**
- Never `git push origin main` after the one-time init commit
- Never `git push --force`
- Never `gh pr merge` or `gh pr edit --ready-for-review`
- `git add` must be scoped to the target directory only (never `git add .` post-init)
- Show `git status --short` to user before every `git commit`
- If `gh pr create` exits non-zero: stop and report stderr — do NOT retry automatically

## Output File Reference (v3 — per-target state)
| File | Writer | Reader |
|---|---|---|
| `state/<lang>/00-lock.json` | All three agents + PR step | All three (startup gate); `pr_url` + `repo_initialized` fields added |
| `state/<lang>/dependency-map.json` | Cartographer | Modernizer, Compliance Officer, Dashboard |
| `state/<lang>/architecture-summary.md` | Cartographer | (Not read by dashboard JS — for human review only) |
| `state/<lang>/changelog.md` | Modernizer (append-only) | Dashboard Tab 2, PR body |
| `state/<lang>/build-log.txt` | Modernizer (overwrite per run) | Modernizer self-healing loop |
| `state/<lang>/compliance-report.json` | Compliance Officer | Dashboard Tab 3, PR body |
| `state/<lang>/pr-body.md` | Modernizer PR step (temp) | `gh pr create --body-file` |
| `state/<lang>/plan-manifest.md` | Plan mode | Modernizer work order |

## Test Suite Notes
Java:
- Single test: `mvn -f legacy-repo/pom.xml test -Dtest=PatientTest#getAgeInYears_returnsCorrectWholeYears`
- `PatientRepository.findAll()` cannot be unit-tested — requires live MySQL; only `hashForLookup()` is tested
- `PatientService` stubs use anonymous subclasses via the package-private injection constructor (no Mockito)

Python:
- Single test: `python3 -m pytest legacy-repo-python/tests/test_patient.py::test_get_age_in_years_returns_correct_whole_years -v`
- `PatientRepository.find_all()` cannot be unit-tested — requires live DB connection; only `hash_for_lookup()` is tested
- Stubs use anonymous subclasses (no pytest-mock / unittest.mock) — same pattern as Java
