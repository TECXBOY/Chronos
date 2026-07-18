# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Architecture Version
**v3** — multi-target, language-agnostic pipeline. `REBUILD_BLUEPRINT.md` supersedes `SPEC.md`
for pipeline/architecture. Compliance rules in `SPEC.md §4` are unchanged and language-agnostic.

## Workspace Structure
```
chronos/
├── .bob/
│   ├── custom_modes.yaml          # Cartographer, Modernizer, Compliance Officer (v3, language-agnostic)
│   └── rules-{agent,ask,plan}/AGENTS.md
├── legacy-repo/                   # Java 11 target — seeded compliance issues must NOT be fixed
│   ├── pom.xml                    # JUnit 5.10.2 + Surefire 3.2.5; compiler source/target=11
│   └── src/
│       ├── main/java/com/clinic/legacy/   # 7 classes, single flat package
│       └── test/java/com/clinic/legacy/   # 5 JUnit 5 tests (no Mockito — anonymous subclasses only)
├── legacy-repo-python/            # Python 2 target — seeded compliance issues must NOT be fixed
│   ├── clinic/                    # 6 modules + __init__.py; sys.path.insert used in tests (no pip install)
│   └── tests/                     # 5 pytest tests + conftest.py
├── state/
│   ├── java/                      # All pipeline outputs (all 3 flags true, PR #1 merged)
│   └── python/                    # Only 00-lock.json present (all flags false — pipeline not yet run)
├── outputs/                       # v1 artifacts only — not read by dashboard or pipeline
└── dashboard/index.html           # Single self-contained HTML; Java/Python toggle in header
```

## Build & Test Commands
```bash
# ── Java ──────────────────────────────────────────────────────────────────────
mvn -f legacy-repo/pom.xml test                                    # all 5 tests
mvn -q -f legacy-repo/pom.xml test                                 # quiet (self-healing loop gate)
mvn -f legacy-repo/pom.xml test -Dtest=PatientRepositoryTest       # single class
mvn -f legacy-repo/pom.xml test -Dtest=PatientTest#getAgeInYears_returnsCorrectWholeYears  # single method

# ── Python ────────────────────────────────────────────────────────────────────
python3 -m pytest legacy-repo-python/tests/ -v                     # all 5 tests
python3 -m pytest legacy-repo-python/tests/ -q                     # quiet (self-healing loop gate)
python3 -m pytest legacy-repo-python/tests/test_patient.py -v      # single file
python3 -m pytest legacy-repo-python/tests/test_patient.py::test_get_age_in_years_returns_correct_whole_years -v
```
All commands run from the repo root. No `cd` required.
**Maven:** `/usr/local/Cellar/maven/3.9.16/` (JDK 25 via Homebrew; `java -version` may show 1.8 on PATH — Maven picks up JDK 25 correctly regardless).
**Python:** 3.14.3, pytest 9.1.0.

## Pipeline & Modes (v3)
All three modes read/write `state/<lang>/` and detect target language from file extensions.

| Mode | Startup gate | Key output |
|---|---|---|
| `cartographer` | none | `state/<lang>/dependency-map.json`, `state/<lang>/architecture-summary.md` |
| `modernizer` | `cartographer_done: true` | Modified source, `state/<lang>/changelog.md`, `state/<lang>/build-log.txt`, draft PR |
| `compliance-officer` | `modernizer_done: true` | `state/<lang>/compliance-report.json` |

**Bob constraint:** `execute` group does NOT support `fileRegex` — Modernizer's shell scope is prompt-constrained only (not schema-enforced). The PR step's `git`/`gh` commands are constrained by an explicit allowlist in `customInstructions` only.

## Self-Healing Loop (Modernizer)
- Gate command is language-specific: `mvn -q -f <target>/pom.xml test` (Java) or `python3 -m pytest <target>/tests/ -q` (Python)
- Cap: 5 attempts per file; `NEEDS MANUAL REVIEW` fallback if capped
- `modernizer_done: true` only set when **zero** files have `NEEDS MANUAL REVIEW` status
- `modernizer_attempts[<file>]` resets to `0` on a clean pass, not at session start

## GitHub PR Automation (Modernizer — runs after all 3 flags true)
- **Always draft:** `gh pr create --draft` — never merge-ready
- **Never push to main post-init:** all post-init pushes go to `chronos/modernize-<lang>-<ts>` branches only
- **Scoped staging:** `git add legacy-repo/ state/java/` or `git add legacy-repo-python/ state/python/` — never `git add .` post-init
- **Auth:** existing `gh` keyring (TECXBOY, `repo` scope) — no new token needed
- **`state/<lang>/pr-body.md`** is built from real changelog + compliance table (not placeholder text) and passed via `--body-file`
- **PR URL** written to `state/<lang>/00-lock.json` as `pr_url` after creation

**`state/<lang>/00-lock.json` schema (v3 — full):**
```json
{
  "cartographer_done": false,
  "modernizer_done": false,
  "compliance_done": false,
  "modernizer_attempts": {},
  "last_updated": null,
  "repo_initialized": true,
  "repo_remote": "https://github.com/TECXBOY/Chronos.git",
  "pages_url": "https://tecxboy.github.io/Chronos/",
  "pr_url": null
}
```
Note: `repo_initialized` is **already `true`** in both `state/java/` and `state/python/` lock files. Skip STEP A of PR automation for all future runs.

**Permitted git/gh commands** (only these, in the PR step):
`git remote -v/add`, `git add <scoped>`, `git status --short`, `git log --oneline -5`, `git commit`, `git push -u origin main` (once — already done), `git checkout -b`, `git push origin <branch>`, `gh auth status`, `gh pr create --draft`, `gh pr view`

**Prohibited always:** `git push --force`, `git push origin main` (post-init), `gh pr merge`, `gh pr edit --ready-for-review`

## Python Target — Non-Obvious Constraints
- **`import urllib2` is a SyntaxError in Python 3** — pytest fails at collection time (not a test failure) for ALL tests that import `patient_repository.py` (i.e., `test_patient_repository.py` AND `test_notification_service.py`). This is expected pre-modernization.
- **`patient_repository.py` has TWO SyntaxErrors:** line 9 (`import urllib2`) AND line 50 (`except Exception, e:`). Both must be fixed before pytest can import `PatientRepository`.
- **`get_age_in_years()` legacy form returns `29` not `30`** for a patient born exactly 30 years ago. Replace `days_lived / 365.25` → date arithmetic: `today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))`.
- **`PatientRepository.find_all()` cannot be unit-tested** — requires live DB. Only `hash_for_lookup()` is tested. Same constraint as Java.
- **Test imports:** `conftest.py` does `sys.path.insert(0, ...)` — no `pip install` or package needed to run tests.

## Java Test Notes (non-obvious)
- **No Mockito** — stubs use anonymous subclasses via package-private injection constructor in `PatientService`. Don't add Mockito.
- **`PatientRepository.findAll()` cannot be unit-tested** — requires live MySQL. Only `hashForLookup()` is tested.
- `pom.xml` deliberately keeps `commons-dbcp 1.4` (old, unpinned) — **seeded compliance issue, do not upgrade**.

## Dashboard (dashboard/index.html)
- **Live URL:** https://tecxboy.github.io/Chronos/ (GitHub Pages, auto-deploys on push to `main`)
- Path auto-detection: `window.location.pathname.includes('/dashboard')` → local uses `../state/`, Pages uses `state/`
- Local dev: `python3 -m http.server 8000` from repo root → `http://localhost:8000/dashboard/`
- `architecture-summary.md` is **NOT** fetched by the dashboard JS (only dep-map, changelog, compliance)
- Python target on Pages: shows file-input fallback (404) until Python pipeline runs and commits `state/python/` files

## Output Schemas (identical for both targets)

**`state/<lang>/changelog.md`** — dashboard parser is exact-match:
```
## <file path>
**Before:** ```<snippet>```
**After:** ```<snippet>```
**Reason:** <one line>
```

**`state/<lang>/compliance-report.json`**
```json
{ "findings": [{ "file": "", "line": 0, "rule_id": "", "severity": "High|Medium|Low", "description": "", "suggested_fix": "" }], "summary": { "high": 0, "medium": 0, "low": 0 } }
```

**`state/<lang>/dependency-map.json`**
```json
{ "files": [{ "path": "", "package": "", "imports": [], "calls": [], "deprecated_apis_used": [] }] }
```

## Seeded Issues — Do Not Fix (either target)
Java: `DatabaseConfig.java` (SEC-001 ×3), `Patient.java` (GDPR-032, GDPR-005, HIPAA-164), `PatientRepository.java` (GDPR-032, SEC-002), `AuditLogger.java` (GDPR-005), `NotificationService.java` (SEC-001), `PatientService.java` (HIPAA-164)
Python: `config.py` (SEC-001), `patient.py` (GDPR-032/HIPAA-164/GDPR-005), `patient_repository.py` (SEC-002), `audit_logger.py` (GDPR-005), `notification_service.py` (SEC-001)
These are intentional Compliance Officer demo targets — **do not remediate them**.

## Reference Priority
1. `REBUILD_BLUEPRINT.md` — authoritative architecture (v3 section §5 is current)
2. `SPEC.md §4` — compliance rule set (unchanged, language-agnostic)
3. `state/<lang>/00-lock.json` — live pipeline progress per target
4. `PROJECT_BRIEF.md` — hackathon scope/constraints
