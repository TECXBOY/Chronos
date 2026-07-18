# Chronos

**A coordinated multi-agent AI pipeline that maps, modernizes, and compliance-audits legacy codebases — built entirely with IBM Bob custom modes.**

---

## What's Working Right Now

Verified state of the live repository as of submission:

- ✅ **Java pipeline — complete.** Cartographer mapped 7 files and 15 deprecated API usages. Modernizer applied 11 changes across 6 files; all 5 JUnit 5 tests pass (`mvn test`). Compliance Officer produced 13 findings (11 High, 2 Medium). Full outputs in [`state/java/`](state/java/).
- ✅ **Python 2 legacy target — seeded and ready.** `legacy-repo-python/` contains a 6-module Python 2 clinic records app with 6 seeded legacy patterns and 5 compliance issues mirroring the Java target. 5 pytest tests written; they fail against legacy code (SyntaxErrors at collection + logic error) and are designed to pass after the Modernizer runs.
- ✅ **Self-healing loop — exercised with real failures.** Two separate files produced distinct failure signatures on attempt 1 (a silent logic regression and a value arithmetic error), diagnosed from `mvn test` output, fixed on attempt 2. Logs in [`state/java/build-log.txt`](state/java/build-log.txt) and [`state/java/changelog.md`](state/java/changelog.md).
- ✅ **GitHub PR automation — live.** After the Java pipeline completed, the Modernizer created branch `chronos/modernize-java-20260718T110628Z`, committed the modernized code, and opened a draft PR with a body built from the real changelog and compliance findings. PR #1 was subsequently merged by a human reviewer: [github.com/TECXBOY/Chronos/pull/1](https://github.com/TECXBOY/Chronos/pull/1).
- ✅ **Dashboard — live on GitHub Pages.** [tecxboy.github.io/Chronos](https://tecxboy.github.io/Chronos/) — auto-deploys on every push to `main`. Java target loads all three tabs (Dependency Map, Before/After, Compliance Report) from real data. Python target shows the file-input fallback (Cartographer has not yet run for that target).

---

## 1. Problem Statement

Regulated industries — healthcare, banking, government — run critical infrastructure on codebases written in Java 8/11, Python 2, and older equivalents. Three distinct failure modes make modernizing these systems expensive and risky:

**No map before touching.** Developers trace dependency chains by reading source code before they can safely change anything. On a real codebase this is not a quick grep — a change to a shared configuration class or a data model can propagate through five layers of callers in ways that aren't obvious from file names alone. Getting this wrong causes silent regressions that reach production.

**Automated refactoring tools break logic without knowing it.** Compiler-driven tools can replace deprecated API calls syntactically, but they do not understand semantic contracts. A tool that replaces `java.util.Date.getYear()` with `LocalDate.getYear()` without accounting for the epoch offset (1900 vs. full year) produces code that compiles cleanly and returns `-1871` for an age that should be `30`. Without a test gate that actually runs against the changed code, the regression is invisible until a user reports a wrong value.

**Compliance issues surface too late.** Security and regulatory violations — hardcoded credentials, unencrypted PHI fields, unsalted hashes on SSNs — typically appear in penetration tests or external audits, not during development. A finding that would cost hours to fix in a pull request costs weeks to remediate after a breach notification or a regulatory fine. Worse: even a correct algorithm upgrade (MD5 → SHA-256) can leave an insecure *usage pattern* intact (bare hash on a 9-digit SSN), which requires a different kind of reasoning than the Modernizer alone provides.

The result is that a single modernization engagement in a regulated industry routinely consumes months of senior engineering time, carries significant legal exposure, and produces documentation no one trusts because the process is not repeatable.

---

## 2. Solution Description

Chronos is a three-agent pipeline, orchestrated with IBM Bob custom modes, that automates the dependency-mapping, refactoring, and compliance-auditing phases of a legacy modernization engagement.

**Three agents coordinate through a shared `state/<language>/` directory**, not a shared conversation thread. Each agent reads its required upstream output files, does its work, and writes its outputs to `state/<lang>/`. A flag file — `state/<lang>/00-lock.json` — carries boolean completion flags that each downstream agent checks before starting. If the required upstream flag is `false`, the agent stops and reports rather than proceeding on absent or stale data.

```
legacy-repo/  (or legacy-repo-python/)
    │
    ▼  Cartographer — read-only analysis
state/<lang>/dependency-map.json        ← sets cartographer_done: true
state/<lang>/architecture-summary.md
    │
    ▼  Modernizer — read + write + execute
modified source files                    ← self-healing build/test loop
state/<lang>/changelog.md               ← sets modernizer_done: true (only on clean pass)
state/<lang>/build-log.txt
    │
    ▼  Compliance Officer — read + limited write (state/ only)
state/<lang>/compliance-report.json     ← sets compliance_done: true
    │
    ▼  PR Automation (end of Modernizer pipeline)
GitHub draft PR                          ← body built from real changelog + compliance findings
    │
    ▼  Dashboard — static HTML/JS, reads state/<lang>/
dashboard/index.html  →  https://tecxboy.github.io/Chronos/
```

The **Modernizer's self-healing loop** is the core mechanical guarantee: for each file with deprecated API usages, it applies a refactor, then runs the full test suite (`mvn test` for Java, `python3 -m pytest` for Python). If the suite fails, it reads the test output, diagnoses the specific failure, and retries — up to 5 attempts per file. On attempt 5 without a clean pass, it appends a `NEEDS MANUAL REVIEW` entry to the changelog and stops. It never claims success without a real passing exit code.

**Two target languages are supported today:** Java (11-era patterns → modern Java) and Python 2 (Python 2-only syntax → Python 3). Both have seeded legacy target repositories, test suites, and compliance-seeded source files. The architecture is designed to generalize — the data contracts and coordination mechanism are language-agnostic; adding a new language requires updating the agent role definitions and build gate command.

---

## 3. AI Approach and Architecture

### Three agents, three tool permission scopes

All three agents are Bob custom modes defined in [`.bob/custom_modes.yaml`](.bob/custom_modes.yaml). Their permissions are set at the schema level in Bob's `groups` field — not just in prompt instructions.

**Cartographer** (`slug: cartographer`)
- `read` + `edit` with `fileRegex: "state/(java|python)/(00-lock\.json|dependency-map\.json|architecture-summary\.md)"`
- Role: static analysis only. Walks the target directory, identifies files, packages, imports, internal call chains, and flags deprecated API usages into `state/<lang>/dependency-map.json`. Sets `cartographer_done: true`.
- The `fileRegex` constraint means it physically cannot write to the source directory. It can only produce its two output files.

**Modernizer** (`slug: modernizer`)
- `read` + `edit` (unrestricted) + `execute` + `skill` + `todo`
- Role: code transformation. Reads `state/<lang>/dependency-map.json`, applies language-specific refactoring rules file by file, and runs the build gate after each change. `execute` is required for `mvn test` / `pytest`. Write scope is constrained by prompt — the `execute` group has no `fileRegex` support in Bob's schema, so scope is enforced through `customInstructions` rather than schema.
- **PR automation** is also the Modernizer's responsibility. After all three pipeline flags are `true`, it creates a feature branch, stages only the target directory files, commits with a message derived from real state data, and calls `gh pr create --draft`.

**Compliance Officer** (`slug: compliance-officer`)
- `read` + `edit` with `fileRegex: "state/.*"`
- Role: security and regulatory audit. Reads the modernized source against five rules (SEC-001, GDPR-032, GDPR-005, HIPAA-164, SEC-002), produces `state/<lang>/compliance-report.json`. The `fileRegex: "state/.*"` constraint physically prevents writes to the source directory — it cannot modify code even if instructed to.

### The `state/<lang>/00-lock.json` coordination primitive

```json
{
  "cartographer_done": true,
  "modernizer_done": true,
  "compliance_done": true,
  "modernizer_attempts": { "Patient.java": 0, "PatientRepository.java": 0 },
  "last_updated": "2026-07-18",
  "repo_initialized": true,
  "repo_remote": "https://github.com/TECXBOY/Chronos.git",
  "pages_url": "https://tecxboy.github.io/Chronos/",
  "pr_url": "https://github.com/TECXBOY/Chronos/pull/1"
}
```

The `modernizer_attempts` field tracks per-file retry counts and resets to `0` on a clean pass. `modernizer_done: true` is only written when zero files have `NEEDS MANUAL REVIEW` status — not when the loop ends, and not when any file has a capped attempt count.

### Bob native mode mapping

| Bob Mode | Chronos function |
|---|---|
| **Ask** | Read-only state summary — checks `state/<lang>/00-lock.json`, summarises the dependency map if `cartographer_done: true`. Never writes. |
| **Plan** | Reads `state/<lang>/dependency-map.json`, produces `state/<lang>/plan-manifest.md` — a file-by-file modification table with target replacements and risk ratings (Low / Medium / High). Edit restricted to that one file. |
| **Agent** | Full pipeline: Modernizer self-healing loop → Compliance Officer audit → feature branch → draft PR. |

### Self-healing loop mechanics

```
FOR each file in dependency-map.json:
  attempts = 0
  WHILE attempts < 5:
    1. Apply refactor to file
    2. Run gate command (mvn test or pytest -q)
    3. IF exit ≠ 0:
         write stdout+stderr → state/<lang>/build-log.txt
         read build-log.txt, diagnose specific error
         increment modernizer_attempts[file] in 00-lock.json
         IF attempts == 5:
           append NEEDS MANUAL REVIEW to changelog.md
           DO NOT set modernizer_done: true
           STOP this file, report to user
         ELSE: fix the specific failure, go to step 1
    4. IF exit == 0:
         append ## <file> / Before / After / Reason entry to changelog.md
         reset modernizer_attempts[file] = 0
         BREAK — move to next file
```

The loop never claims success without a real `exit 0`. A capped-attempt "NEEDS MANUAL REVIEW" fallback is the honest alternative to silently reverting a failed change.

### Language rule sets

**Java (`.java` files):**
`java.util.Date` / `Date.getYear()` / `getMonth()` / `getDate()` → `java.time.LocalDate` / `Period.between()` / `DateTimeFormatter` · `new Integer(String)` → `Integer.parseInt()` · `StringBuffer` → `StringBuilder` · `java.util.Vector` / `elementAt()` → `ArrayList` / enhanced for-loop · `java.sql.Statement` (raw SQL concat) → `PreparedStatement` · `MessageDigest("MD5")` → `MessageDigest("SHA-256")`

**Python 2 (`.py` files):**
`print <expr>` → `print(<expr>)` · `xrange()` → `range()` · `dict.iteritems()` / `.itervalues()` / `.iterkeys()` → `.items()` / `.values()` / `.keys()` · `except Exception, e:` → `except Exception as e:` · `import urllib2` → `import urllib.request` · implicit integer division in age calculations → `today.year - dob.year - (...)` date arithmetic

### Compliance rule set (language-agnostic)

| Rule ID | Standard | Check |
|---|---|---|
| SEC-001 | General secure coding | Hardcoded credentials, API keys, or secrets in source |
| GDPR-032 | GDPR Art. 32 | Personal data stored or transmitted without encryption |
| GDPR-005 | GDPR Art. 5 | Full personal records logged unnecessarily (data minimization) |
| HIPAA-164 | HIPAA §164.312 | PHI fields not access-controlled or encrypted |
| SEC-002 | OWASP | Insecure or broken cryptographic usage patterns |

The same five rules apply to both Java and Python targets. The checks are semantic — they identify the *pattern* (e.g. unsalted hash on a low-entropy PII value), not just the presence of a specific deprecated function name.

---

## 4. Chosen Theme

**Wildcard — "Build Intelligent Systems for the Future of Work"**

Legacy modernization is one of the highest-cost, most risk-laden engineering tasks that regulated organizations face, and it is almost entirely driven by manual, tribal-knowledge-dependent processes. Chronos reframes it as an orchestrated, deterministic, auditable AI workflow: a dependency map produced from a real static analysis pass, a refactoring loop gated on a real test runner, a compliance audit whose findings cite specific files and line numbers, and a draft pull request that a human reviewer can approve or reject with full context. The system does not bypass the human — it makes the human's review task tractable by doing the mechanical work, documenting every decision, and producing artifacts (changelog, compliance report, PR body) that are directly actionable. That is what intelligent systems for the future of work look like: not systems that replace judgment, but systems that scale it.

---

## 5. How IBM Bob Was Used

Bob was not used as a code-completion assistant. It was the execution environment for the entire pipeline — from workspace initialization to the final draft PR.

### `/init` — workspace context

Running `/init` in `chronos/` generated the root [`AGENTS.md`](AGENTS.md), which captures the workspace structure, data contracts, mode slugs, and pipeline conventions. Every agent session loads this file as context. Mode-specific context files in [`.bob/rules-agent/`](.bob/rules-agent/AGENTS.md), [`.bob/rules-ask/`](.bob/rules-ask/AGENTS.md), and [`.bob/rules-plan/`](.bob/rules-plan/AGENTS.md) carry additional role-specific constraints.

### Custom mode configuration

All three modes are defined in [`.bob/custom_modes.yaml`](.bob/custom_modes.yaml). Key schema entries:

```yaml
# Cartographer — fileRegex restricts writes to state/ outputs only
- slug: cartographer
  groups:
    - read
    - - edit
      - fileRegex: "state/(java|python)/(00-lock\\.json|dependency-map\\.json|architecture-summary\\.md)"
    - skill
    - todo

# Modernizer — execute group added for build gate + gh CLI
- slug: modernizer
  groups: [read, edit, execute, skill, todo]

# Compliance Officer — hard write boundary via fileRegex
- slug: compliance-officer
  groups:
    - read
    - - edit
      - fileRegex: "state/.*"
    - skill
    - todo
```

Each mode carries `customInstructions` with its startup gate check, language detection logic, rule set, and (for Modernizer) the full self-healing loop and PR automation specification.

### Cartographer run (Java target)

**Prompt used:**
> Scan `legacy-repo/`. Identify every Java file, its package, imports, and which internal classes/methods it calls. Output `state/java/dependency-map.json`. Also produce `state/java/architecture-summary.md`.

**Real output — [`state/java/dependency-map.json`](state/java/dependency-map.json):**
- 7 files, single package `com.clinic.legacy`
- 3-level dependency chain: `Main → PatientService → PatientRepository / AuditLogger / NotificationService`
- `DatabaseConfig` identified as a shared leaf node — both `PatientRepository` and `NotificationService` read from it, meaning any credential leak in that file has two call-site exposure paths
- 15 deprecated API usages across 6 files: `java.util.Vector` (4 files), `java.util.Date` / `Date.getYear()` / `getMonth()` / `getDate()` (2 files), `new Integer(String)` constructor, raw `Statement` (SQL injection vector), `MessageDigest("MD5")`, `StringBuffer` (2 files)

### Modernizer run — self-healing loop (Java target)

**Prompt used:**
> Using `state/java/dependency-map.json`, refactor `legacy-repo/` to replace all deprecated APIs flagged in `deprecated_apis_used`. Preserve method signatures and business logic exactly. Gate each change on `mvn -q -f legacy-repo/pom.xml test`. For every passing change, append an entry to `state/java/changelog.md`.

**11 changes across 6 files — all passed `mvn test` (5/5 tests):**

| File | Change |
|---|---|
| `Patient.java` | `new Integer(idStr)` → `Integer.parseInt(idStr)`; `java.util.Date` → `java.time.LocalDate`; `Date.getYear()` age calc → `Period.between(dateOfBirth, LocalDate.now()).getYears()`; `StringBuffer` → `StringBuilder` |
| `AuditLogger.java` | `Date.getMonth()/getDate()/getYear()` → `LocalDate.now().format(DateTimeFormatter.ofPattern(...))` |
| `PatientRepository.java` | `Vector<Patient>` + `addElement()` → `List<Patient>` + `ArrayList` + `add()`; raw `Statement` + string concat → `PreparedStatement` with `?` parameter; `MessageDigest("MD5")` → `MessageDigest("SHA-256")`; `StringBuffer` → `StringBuilder` |
| `PatientService.java` | `Vector` + `elementAt()` index loops (×2) → `List` + enhanced for-loops |
| `Main.java` | `Vector<Patient>` local variable → `List<Patient>` |
| `NotificationService.java` | `StringBuffer` → `StringBuilder` |

**Self-healing loop — two real failure/retry/pass cycles:**

The loop was exercised on two separate files in the same pipeline run, producing two different failure signatures. Both are captured verbatim in [`state/java/build-log.txt`](state/java/build-log.txt):

**File 1 — `Patient.java`, `getAgeInYears()` (2 attempts):**
- Attempt 1 FAILED: regression to `java.util.Date` arithmetic mixed `Date.getYear()` (returns offset from 1900, e.g. `126` for 2026) with `LocalDate.getYear()` (returns full year, e.g. `1996`). Both sides were incremented by `+1900`, compounding the mismatch: `(126 + 1900) - (1996 + 1900) - 1 = -1871`. Code compiled without errors or warnings.
- Test that caught it: `PatientTest.getAgeInYears_returnsCorrectWholeYears — expected: <30> but was: <-1871>`
- Attempt 2 PASSED: restored `Period.between(dateOfBirth, LocalDate.now()).getYears()`

**File 2 — `PatientRepository.java`, `hashForLookup()` (2 attempts):**
- Attempt 1 FAILED: the byte-to-hex encoding for-loop body was emptied — `hex.append(String.format("%02x", b))` was removed. The `MessageDigest` computed the SHA-256 digest correctly; the loop ran without error; `hex.toString()` returned `""` for every input. Zero compiler warnings.
- Test that caught it: `PatientRepositoryTest.hashForLookup_producesDifferentOutputForDifferentInput — expected: not equal but was: <>`
- Attempt 2 PASSED: restored `hex.append(String.format("%02x", b))`

Both files resolved in 2 attempts. Neither hit the 5-attempt cap. The second failure — code that compiles and runs but silently returns a wrong value for all inputs — demonstrates exactly why `mvn test` (not `mvn compile`) is the correct gate.

### Compliance Officer run (Java target)

**Prompt used:**
> Scan `legacy-repo/` against the rules in `SPEC.md` §4. For each violation, record the file, line number, rule ID, severity, a description of the specific issue, and a concrete suggested fix. Output `state/java/compliance-report.json`.

**13 findings — [`state/java/compliance-report.json`](state/java/compliance-report.json):**

| Rule | Count | Representative finding |
|---|---|---|
| SEC-001 | 4 High | `NotificationService.java:18` — API key printed to stdout on every `sendReminder()` call. Even after rotating the hardcoded literal in `DatabaseConfig.java`, any logging infrastructure capturing stdout will record the new key in plaintext. |
| GDPR-032 | 2 High, 1 Medium | `PatientRepository.java:25` — `jdbc:mysql://` connection URL with no SSL/TLS parameters; all SSNs and diagnoses transmitted in cleartext over the network. |
| GDPR-005 | 2 High | `AuditLogger.java:24` — `patient.toString()` embeds SSN and diagnosis; called on every record access. Any log line, exception message, or debug output that includes this object leaks full PHI. |
| HIPAA-164 | 3 High | `PatientService.java:24` — `getAllPatients()` returns every patient record including PHI fields to any caller without an authorization check. |
| SEC-002 | 1 Medium | `PatientRepository.java:54` — **most notable finding**: SHA-256 applied bare and unsalted to SSN values in `hashForLookup()`. The Modernizer correctly upgraded MD5 → SHA-256 (fixing the broken algorithm). The Compliance Officer identified that the *usage pattern* remains insecure: SSNs occupy a small, enumerable space (9-digit numbers with known format), so a precomputation or rainbow table attack reverses the hash in seconds. Fix: `PBKDF2WithHmacSHA256` with a per-record random salt. Neither agent's pass was sufficient alone — this is a genuine multi-agent catch. |

### PR automation

After the pipeline completed, the Modernizer:
1. Detected `repo_initialized: false` → added remote `https://github.com/TECXBOY/Chronos.git`, made the initial baseline commit to `main`, pushed
2. Created branch `chronos/modernize-java-20260718T110628Z`
3. Staged `legacy-repo/` + `state/java/` only
4. Built commit message from real state counts: `feat(chronos-java): modernize Java 11 clinic records — 4 change groups, 2 files — gate: mvn test passing — compliance: 11H/2M/0L`
5. Wrote `state/java/pr-body.md` from the real changelog and compliance findings (13-row table)
6. Ran `gh pr create --draft --base main --head chronos/modernize-java-20260718T110628Z --body-file state/java/pr-body.md`

**Result:** [github.com/TECXBOY/Chronos/pull/1](https://github.com/TECXBOY/Chronos/pull/1) — created as draft, `autoMergeRequest: null`, subsequently reviewed and merged manually by the human reviewer (`TECXBOY`, 2026-07-18T11:20:50Z). The pipeline never auto-merged.

### Dashboard and GitHub Pages

The dashboard ([`dashboard/index.html`](dashboard/index.html)) is a single self-contained HTML/JS file with no build step and no backend. It fetches three files from `state/<lang>/` — `dependency-map.json`, `changelog.md`, `compliance-report.json` — and renders them across three tabs (Dependency Map, Before/After, Compliance Report). A Java/Python target selector in the header switches the fetch base path.

**Local:**
```bash
python3 -m http.server 8000   # from chronos/ root
# → http://localhost:8000/dashboard/
```

**Hosted:** `.github/workflows/pages.yml` assembles `dashboard/index.html` + `state/` into `_site/` and deploys on every push to `main`. Path detection (`window.location.pathname.includes('/dashboard')`) switches between `../state/` (local) and `state/` (Pages root) automatically.

**Live URL:** [tecxboy.github.io/Chronos](https://tecxboy.github.io/Chronos/)

---

## Repository Structure

```
chronos/
├── AGENTS.md                              # Bob project-context file
├── REBUILD_BLUEPRINT.md                   # Architecture spec — authoritative
├── SPEC.md                                # Compliance rule set §4
├── .bob/
│   ├── custom_modes.yaml                  # All three modes
│   └── rules-{agent,ask,plan}/AGENTS.md  # Mode-specific context
├── legacy-repo/                           # Java 11 target (seeded with real issues)
│   ├── pom.xml                            # JUnit 5.10.2 + Surefire 3.2.5
│   └── src/
│       ├── main/java/com/clinic/legacy/  # 7 source files, single package
│       └── test/java/com/clinic/legacy/  # 5 JUnit 5 tests
├── legacy-repo-python/                    # Python 2 target (seeded, pipeline pending)
│   ├── clinic/                            # 6 modules + __init__.py
│   └── tests/                             # 5 pytest tests
├── state/
│   ├── java/                              # All Java pipeline outputs (complete)
│   │   ├── 00-lock.json                   # All three flags true; pr_url recorded
│   │   ├── dependency-map.json
│   │   ├── architecture-summary.md
│   │   ├── changelog.md                   # Self-healing loop log + change entries
│   │   ├── build-log.txt                  # Raw mvn test output, failure + pass runs
│   │   ├── compliance-report.json         # 13 findings
│   │   ├── pr-body.md                     # PR body used for gh pr create
│   │   └── pr-draft.md                    # Human-readable pipeline summary
│   └── python/                            # Python pipeline (Cartographer not yet run)
│       └── 00-lock.json                   # All three flags false
├── outputs/                               # Pre-migration artifacts (reference only)
├── dashboard/
│   └── index.html                         # Static viewer, Java/Python target selector
└── .github/
    └── workflows/
        └── pages.yml                      # GitHub Pages deployment workflow
```

---

## Scope and Future Work

**What Chronos does today:**
- Java 11-era deprecated APIs → modern Java, gated on `mvn test`
- Python 2 syntax patterns → Python 3, gated on `pytest` (pipeline ready; Cartographer + Modernizer + Compliance Officer not yet run on the Python target)
- Five compliance rules (SEC-001, GDPR-032, GDPR-005, HIPAA-164, SEC-002) applied to both targets
- GitHub draft PR automation (branch, commit, push, `gh pr create --draft`)
- Static dashboard hosted on GitHub Pages

**What is not done yet:**
- The Python pipeline (Cartographer, Modernizer, Compliance Officer) has not been run. The target repository and test suite exist and are ready; the pipeline outputs (`state/python/dependency-map.json`, `state/python/compliance-report.json`, etc.) do not exist yet.
- True multi-language auto-detection beyond Java and Python 2 is future work. Adding a new language requires authoring the deprecated-API rule set, the build gate command, and the compliance pattern list for that language — the coordination mechanism and dashboard are already language-agnostic.
- No support for COBOL, TypeScript, or other languages in the current implementation.
- The self-healing loop has been tested to a maximum of 2 attempts per file. The 5-attempt cap and `NEEDS MANUAL REVIEW` fallback are implemented and documented but have not been exercised.

---

## Challenge Information

- **Competition:** AI Builders Challenge with IBM Bob — BeMyApp / IBM SkillsBuild
- **Track:** Wildcard — "Build Intelligent Systems for the Future of Work"
- **Submission deadline:** July 31, 2026
- **Repository:** [github.com/TECXBOY/Chronos](https://github.com/TECXBOY/Chronos)
- **Live dashboard:** [tecxboy.github.io/Chronos](https://tecxboy.github.io/Chronos/)
- **Java modernization PR:** [github.com/TECXBOY/Chronos/pull/1](https://github.com/TECXBOY/Chronos/pull/1)
