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
│       └── test/java/com/clinic/legacy/   # 5 JUnit 5 tests
├── legacy-repo-python/            # Python 2 target — seeded compliance issues must NOT be fixed
│   ├── clinic/                    # 6 modules (config, patient, patient_repository,
│   │   └── ...                    #   audit_logger, notification_service, main) + __init__.py
│   └── tests/                     # 5 pytest tests (test_patient, test_patient_repository,
│       └── ...                    #   test_notification_service) + conftest.py
├── state/
│   ├── java/                      # All Java pipeline outputs (cartographer_done: true, fully populated)
│   │   ├── 00-lock.json
│   │   ├── dependency-map.json
│   │   ├── architecture-summary.md
│   │   ├── changelog.md
│   │   ├── build-log.txt
│   │   ├── compliance-report.json
│   │   └── pr-draft.md
│   └── python/                    # Python pipeline state (cartographer_done: false — not yet run)
│       └── 00-lock.json
├── outputs/                       # v1 artifacts (kept, reference only — not read by dashboard)
└── dashboard/index.html           # Single self-contained file; Java/Python toggle in header
```

## Build & Test Commands
```bash
# ── Java ──────────────────────────────────────────────────────────
# Run all 5 tests
mvn -f legacy-repo/pom.xml test

# Quiet mode (used by self-healing loop)
mvn -q -f legacy-repo/pom.xml test

# Single test class
mvn -f legacy-repo/pom.xml test -Dtest=PatientRepositoryTest

# Single test method
mvn -f legacy-repo/pom.xml test -Dtest=PatientTest#getAgeInYears_returnsCorrectWholeYears

# ── Python ────────────────────────────────────────────────────────
# Run all 5 tests (from repo root)
python3 -m pytest legacy-repo-python/tests/ -v

# Quiet mode (used by self-healing loop)
python3 -m pytest legacy-repo-python/tests/ -q

# Single test file
python3 -m pytest legacy-repo-python/tests/test_patient.py -v

# Single test
python3 -m pytest legacy-repo-python/tests/test_patient.py::test_get_age_in_years_returns_correct_whole_years -v
```
Maven: `/usr/local/Cellar/maven/3.9.16/` (Homebrew, JDK 25). `java -version` may show 1.8 on PATH but Maven
picks up JDK 25 correctly. Python: 3.14.3, pytest 9.1.0.

## Pipeline & Modes (v3 — language-agnostic)
All three modes accept a target directory + language as input. They read/write `state/<lang>/`.

| Mode slug | Tool permissions | Startup gate | Output |
|---|---|---|---|
| `cartographer` | `read` + `edit` (fileRegex: `state/(java\|python)/...`) | none | `state/<lang>/dependency-map.json`, `state/<lang>/architecture-summary.md` |
| `modernizer` | `read` + `edit` + `execute` | `cartographer_done: true` in `state/<lang>/` | Modified source, `state/<lang>/changelog.md`, `state/<lang>/build-log.txt`, draft PR |
| `compliance-officer` | `read` + `edit` (fileRegex: `state/.*`) | `modernizer_done: true` | `state/<lang>/compliance-report.json` |

**Build gates by language:**
- Java: `mvn -q -f <target>/pom.xml test`
- Python: `python3 -m pytest <target>/tests/ -q`

**Bob constraint:** `execute` group does NOT support `fileRegex` — Modernizer's shell scope is
prompt-constrained only, not schema-enforced. The PR step's `git`/`gh` commands are constrained
by an explicit allowlist in `customInstructions`, not by schema.

## Self-Healing Loop (Modernizer — same mechanics, different gate per language)
- Gate command is language-dependent (see above); must exit 0 to count as success
- Cap: 5 attempts per file; `NEEDS MANUAL REVIEW` fallback if capped
- Tool check before loop: `mvn -version` (Java) or `python3 -m pytest --version` (Python)
- `modernizer_done: true` only set when zero files have `NEEDS MANUAL REVIEW` status
- `modernizer_attempts[<file>]` resets to `0` on a clean pass, not at session start

## GitHub PR Automation (Modernizer — runs after all three flags are true)
- **Always draft:** `gh pr create --draft` — never merge-ready, never auto-merged
- **Never pushes to main:** After one-time initial baseline commit, all pushes go to `chronos/modernize-<lang>-<ts>` branches only
- **Staged files scoped to target:** `git add legacy-repo/ state/java/` or `git add legacy-repo-python/ state/python/` — never `git add .` post-init
- **Auth:** Reuses existing `gh` keyring credentials (TECXBOY, `repo` scope). No new token needed.
- **Remote:** `https://github.com/TECXBOY/Chronos.git`
- **One-time init:** On first Agent run, commits entire repo to `main` and pushes. Sets `repo_initialized: true` in both lock files.
- **PR URL** written to `state/<lang>/00-lock.json` as `pr_url` after creation.
- **`state/<lang>/pr-body.md`** is written as temp file and passed to `gh pr create --body-file`; contains real changelog + compliance table, not placeholder text.

**`state/<lang>/00-lock.json` schema (v3 — full):**
```json
{
  "cartographer_done": false,
  "modernizer_done": false,
  "compliance_done": false,
  "modernizer_attempts": {},
  "last_updated": null,
  "repo_initialized": false,
  "repo_remote": "https://github.com/TECXBOY/Chronos.git",
  "pr_url": null
}
```

**Permitted git/gh commands** (only these, in the PR step):
`git remote -v/add`, `git add <scoped>`, `git status --short`, `git commit`, `git push -u origin main` (once), `git checkout -b`, `git push origin <branch>`, `gh auth status`, `gh pr create --draft`, `gh pr view`

**Prohibited always:** `git push --force`, `git push origin main` (post-init), `gh pr merge`, `gh pr edit --ready-for-review`

## Python Target — Non-Obvious Constraints
- Legacy `.py` files use Python 2 syntax — they are **SyntaxErrors** in Python 3 before modernization.
  pytest will fail at collection time (not test failure), which IS the expected pre-modernization state.
- `patient_repository.py` has both `import urllib2` AND `except Exception, e:` — two separate SyntaxErrors
  that must both be fixed before pytest can collect any test that imports it.
- `get_age_in_years()` uses `days_lived / 365.25` (legacy int-division form) — returns `29` not `30`
  for a patient born exactly 30 years ago today. The age test will fail until this is replaced with
  `today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))`.
- `PatientRepository.find_all()` cannot be unit-tested (requires a live DB) — same constraint as Java.
  Only `hash_for_lookup()` is tested in isolation.
- Test stubs use anonymous subclasses (no pytest-mock / unittest.mock needed) — same pattern as Java suite.

## Dashboard (dashboard/index.html)
- **Java/Python toggle** in header switches `OUTPUTS()` between `../state/java/` and `../state/python/`
- Switching target clears cached data and calls `loadAll()` again; shows load-bar if fetch fails for that target
- Must be served from `chronos/` root: `python3 -m http.server 8000` then open `http://localhost:8000/dashboard/`
- `architecture-summary.md` is NOT fetched by the dashboard JS (only the 3 files: dep-map, changelog, compliance)
- Before/After subtitle updates to show `mvn test` or `pytest` based on active target

## Seeded Issues — Do Not Fix (either target)
Java: `DatabaseConfig.java` and PHI fields in `Patient.java` (SEC-001, GDPR-032, GDPR-005, HIPAA-164)
Python: `config.py`, `patient.py`, `patient_repository.py`, `audit_logger.py`, `notification_service.py`
These are intentional Compliance Officer demo targets — do not remediate them.

## Output Schemas (identical for both targets)

**`state/<lang>/changelog.md`** — dashboard parser exact-match format:
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
