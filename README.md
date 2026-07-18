# Chronos

**A coordinated multi-agent AI pipeline that maps, modernizes, and compliance-audits legacy codebases — built entirely with IBM Bob custom modes.**

> **v2** — coordinated multi-agent architecture with shared state coordination, self-healing build loop, and Ask/Plan/Agent mode hooks. See [`REBUILD_BLUEPRINT.md`](REBUILD_BLUEPRINT.md).

---

## Problem

Regulated industries — government, banking, healthcare — run critical infrastructure on Java 8/11, COBOL, and aging Python. Modernizing those systems is expensive and risky for three reasons:

1. **No map.** Developers manually trace dependencies before touching anything. On a large codebase this takes days, and errors cause silent regressions.
2. **Refactors break things.** Automated tooling upgrades syntax but doesn't reason about behavior preservation or downstream call chains.
3. **Compliance is caught late.** Security and regulatory issues (GDPR, HIPAA, hardcoded secrets) surface in pen-tests or audits — not during development. By then, fixing them is expensive.

The result: a single modernization project consumes months of engineering time, carries significant legal exposure, and leaves a paper trail no one trusts.

---

## Solution: Chronos

Chronos runs three specialized Bob agent modes against a target repository. Each agent coordinates through a shared `state/` directory — reading upstream outputs and writing its own — rather than a shared conversation thread. This means each agent can start as soon as its dependency exists, and every handoff is a file on disk rather than a fragile in-memory state.

**Current language support: Java.** The three-agent architecture (dependency mapping → refactoring → compliance audit) is designed to generalize to other languages (Python, COBOL, TypeScript) as future work — the data contracts and coordination mechanism are language-agnostic; only the agent role definitions and tool prompts need updating per language.

```
legacy-repo/
    │
    ▼  [Cartographer — read-only]
state/dependency-map.json        sets cartographer_done: true
state/architecture-summary.md
    │
    ▼  [Modernizer — read + write + execute]
modified legacy-repo/            self-healing build loop, mvn test gate
state/changelog.md               sets modernizer_done: true (only on clean pass)
state/build-log.txt
    │
    ▼  [Compliance Officer — read + write state/ only]
state/compliance-report.json     sets compliance_done: true
    │
    ▼  [Dashboard — static HTML/JS, reads state/]
dashboard/index.html
```

The sample target is a deliberately seeded Java 11 clinic records application (`legacy-repo/`) — 7 files, one package, real code smells across all three audit categories.

---

## Theme

**Wildcard — "Build Intelligent Systems for the Future of Work"**

Legacy modernization is one of the highest-cost, highest-risk engineering tasks in regulated industries. It blocks teams, delays digital transformation programs, and creates compliance exposure. Chronos reframes it as an orchestrated, auditable AI workflow — deterministic inputs, structured outputs, a visible audit trail, and a build gate that actually runs — rather than a tribal-knowledge-dependent manual process.

---

## Architecture

### Pipeline coordination — `state/` and `00-lock.json`

Agents do not share a conversation thread. They share a directory: `state/`. The coordination primitive is [`state/00-lock.json`](state/00-lock.json) — a simple flag file each agent reads at startup and writes to on completion:

```json
{
  "cartographer_done": true,
  "modernizer_done": true,
  "compliance_done": true,
  "modernizer_attempts": { "Patient.java": 0, "PatientRepository.java": 0 },
  "last_updated": "2026-07-18"
}
```

If an agent's required upstream flag is `false`, it stops and reports — it never silently proceeds on stale or absent data.

### Agent modes

| Mode slug | Tool permissions | Startup gate | Output |
|---|---|---|---|
| `cartographer` | `read` + `edit` (`fileRegex: state/(00-lock.json\|dependency-map.json\|architecture-summary.md)`) | none | `state/dependency-map.json`, `state/architecture-summary.md` |
| `modernizer` | `read` + `edit` + `execute` | `cartographer_done: true` | Modified `legacy-repo/`, `state/changelog.md`, `state/build-log.txt` |
| `compliance-officer` | `read` + `edit` (`fileRegex: state/.*`) | `modernizer_done: true` | `state/compliance-report.json` |

`compliance-officer`'s `fileRegex: "state/.*"` is a hard schema constraint — it physically cannot write to `legacy-repo/`. `modernizer`'s `execute` scope is enforced by prompt constraint (Bob's `execute` group does not support `fileRegex`).

### Bob native mode mapping

| Bob Mode | Chronos Function |
|---|---|
| **Ask** | Read-only repo/pipeline state — checks `state/00-lock.json`, summarises `state/dependency-map.json` if available. Never writes. |
| **Plan** | Reads `state/dependency-map.json`, produces `state/plan-manifest.md` — a file-by-file modification list with target APIs and risk ratings. Edit scoped to `state/plan-manifest.md` only. |
| **Agent** | Full pipeline: Modernizer self-healing loop → Compliance Officer audit → `state/pr-draft.md` drafted for human review. |

### Data contracts (unchanged from v1)

**`state/dependency-map.json`** — Cartographer → Modernizer handoff:
```json
{
  "files": [{
    "path": "src/main/java/com/clinic/legacy/PatientRepository.java",
    "package": "com.clinic.legacy",
    "imports": ["java.sql.Statement", "java.util.Vector"],
    "calls": ["DriverManager.getConnection", "MessageDigest.getInstance"],
    "deprecated_apis_used": [
      "java.util.Vector",
      "java.sql.Statement (raw, non-parameterized — SQL injection risk)",
      "MessageDigest with MD5 algorithm (cryptographically broken)"
    ]
  }]
}
```

**`state/changelog.md`** — Modernizer output, append-only, dashboard-parsed:
```
## src/main/java/com/clinic/legacy/PatientRepository.java
**Before:** ```Statement stmt = conn.createStatement()```
**After:** ```PreparedStatement stmt = conn.prepareStatement(query)```
**Reason:** Raw Statement is vulnerable to SQL injection; PreparedStatement with parameterized inputs is the correct modern approach.
```

**`state/compliance-report.json`** — Compliance Officer output, dashboard input:
```json
{
  "findings": [{
    "file": "src/main/java/com/clinic/legacy/DatabaseConfig.java",
    "line": 14, "rule_id": "SEC-001", "severity": "High",
    "description": "Hardcoded database password 'Cl1nic#2011!' committed as a public static final String.",
    "suggested_fix": "Load DB_PASSWORD at runtime from System.getenv() or a secrets manager. Rotate immediately."
  }],
  "summary": { "high": 11, "medium": 2, "low": 0 }
}
```

---

## How IBM Bob Was Used

Bob was the primary development tool at every stage — not a code-completion assistant, but the execution environment for the entire pipeline.

### `/init` — workspace context

Running `/init` in `chronos/` generated the root [`AGENTS.md`](AGENTS.md), which captures the workspace structure, output schemas, mode slugs, and pipeline conventions. Every subsequent agent session loads this file as context, ensuring each mode knows the data contracts before it starts.

### Custom mode configuration

All three modes are defined in [`.bob/custom_modes.yaml`](.bob/custom_modes.yaml), authored in Bob's Agent mode from the specs in [`REBUILD_BLUEPRINT.md`](REBUILD_BLUEPRINT.md):

**Cartographer** — read-only analysis, `fileRegex`-restricted write to `state/` outputs:
```yaml
slug: cartographer
groups: [read, [edit, fileRegex: "state/(00-lock\\.json|dependency-map\\.json|architecture-summary\\.md)"], skill, todo]
```

**Modernizer** — `execute` added for the self-healing build loop:
```yaml
slug: modernizer
groups: [read, edit, execute, skill, todo]
```

**Compliance Officer** — hard write boundary via `fileRegex`:
```yaml
slug: compliance-officer
groups: [read, [edit, fileRegex: "state/.*"], skill, todo]
```

Each mode carries `customInstructions` with the startup gate check and (for Modernizer) the full self-healing loop specification — see [`.bob/rules-agent/AGENTS.md`](.bob/rules-agent/AGENTS.md).

### Cartographer run

**Prompt:**
> Scan `legacy-repo/`. Identify every Java file, its package, imports, and internal calls. Output `state/dependency-map.json`. Also produce `state/architecture-summary.md`.

**Real output:**
- 7 Java files, single package `com.clinic.legacy`, 3-level dependency chain (`Main → PatientService → PatientRepository/AuditLogger/NotificationService`)
- 10 deprecated API usages across 6 files: `java.util.Vector` (×4 files), `java.util.Date`/`Date.getYear()` (×2), `new Integer(String)` constructor, raw `Statement` (SQL injection), MD5 hashing, `StringBuffer` (×2)
- `DatabaseConfig` identified as a shared leaf node — credential exposure radius spans two callers

### Modernizer run + self-healing loop

**Prompt:**
> Using `state/dependency-map.json`, refactor `legacy-repo/` to replace all deprecated APIs. Preserve method signatures. For every change, append an entry to `state/changelog.md`. Gate each change on `mvn -q -f legacy-repo/pom.xml test`.

**11 changes across 6 files — all passed `mvn test`:**

| File | Change |
|---|---|
| `Patient.java` | `new Integer(String)` → `Integer.parseInt()`; `java.util.Date` → `java.time.LocalDate`; `Date.getYear()` age calc → `Period.between()`; `StringBuffer` → `StringBuilder` |
| `AuditLogger.java` | `Date.getMonth/getDate/getYear()` timestamp → `LocalDate.now().format(DateTimeFormatter)` |
| `PatientRepository.java` | `Vector` → `List`/`ArrayList`; `Statement` + string concat → `PreparedStatement`; MD5 → SHA-256; `StringBuffer` → `StringBuilder` |
| `PatientService.java` | `Vector` + `elementAt()` index loops → `List` + enhanced for-loops (×2) |
| `Main.java` | `Vector<Patient>` → `List<Patient>` |
| `NotificationService.java` | `StringBuffer` → `StringBuilder` |

**Self-healing loop — verified with two real failures:**

The loop was exercised end-to-end twice, on different files, producing different failure signatures:

**Run 1 — `Patient.java` (`getAgeInYears`):**
- Regression: `java.util.Date` arithmetic mixing `Date.getYear()` (offset from 1900) with `LocalDate.getYear()` (full year), producing `-1871` instead of `30`
- Test caught: `PatientTest.getAgeInYears_returnsCorrectWholeYears expected: <30> but was: <-1871>`
- Fix on attempt 2: restored `Period.between(dateOfBirth, LocalDate.now()).getYears()`

**Run 2 — `PatientRepository.java` (`hashForLookup`):**
- Regression: for-loop body emptied — `hex` StringBuilder never populated, method returns `""` for every input. Compiled cleanly, zero warnings
- Test caught: `PatientRepositoryTest.hashForLookup_producesDifferentOutputForDifferentInput expected: not equal but was: <>`
- Fix on attempt 2: restored `hex.append(String.format("%02x", b))`

Both runs resolved in 2 attempts. No file hit the 5-attempt cap. Full logs in [`state/changelog.md`](state/changelog.md) and [`state/build-log.txt`](state/build-log.txt).

The second failure (`""` returned for all inputs) is a realistic representation of a silent logic regression that passes compilation and static analysis but is immediately caught by a value-checking test. This is the core value of the `mvn test` gate over `mvn test-compile` alone.

### Compliance Officer run

**Prompt:**
> Scan `legacy-repo/` against the rules in `SPEC.md` §4. Record file, line, rule ID, severity, description, and suggested fix for each violation. Write `state/compliance-report.json`.

**13 findings (11 High, 2 Medium):**

| Rule | Findings | Files |
|---|---|---|
| SEC-001 | 4 High | Hardcoded DB credentials + live API key in `DatabaseConfig.java`; API key printed to stdout in `NotificationService.java` |
| GDPR-032 | 2 High, 1 Medium | SSN stored plain in `Patient.java`; no SSL on JDBC URL in `PatientRepository.java`; DOB stored plain |
| GDPR-005 | 2 High | `toString()` embeds SSN+diagnosis; `AuditLogger` prints full record on every access |
| HIPAA-164 | 3 High | `diagnosis` (PHI) unencrypted, public getters with no auth, `getAllPatients()` with no role check |
| SEC-002 | 1 Medium | SHA-256 applied bare/unsalted to SSN — trivially reversible by precomputation (caught despite Modernizer having upgraded MD5→SHA-256) |

The SEC-002 finding demonstrates a genuine multi-agent catch: the Modernizer correctly replaced MD5 with SHA-256 (fixing the algorithm), but the Compliance Officer identified that the *usage pattern* (bare hash on a low-entropy 9-digit input) remains insecure. Neither agent's pass was sufficient alone.

### Dashboard

A static `dashboard/index.html` reads from `state/` via `fetch('../state/...')`. No build step, no backend. File-input fallback for `file://` CORS environments.

```bash
python3 -m http.server 8000   # from chronos/ root
# → http://localhost:8000/dashboard/
```

---

## Repository Structure

```
chronos/
├── AGENTS.md                        # Bob project-context file — NOT the modification manifest
├── REBUILD_BLUEPRINT.md             # v2 architecture spec — authoritative
├── SPEC.md                          # compliance rule set §4 — unchanged
├── .bob/
│   ├── custom_modes.yaml            # all three modes (v2)
│   └── rules-{agent,ask,plan}/AGENTS.md
├── legacy-repo/                     # Java 11 target (seeded with real issues)
│   └── src/
│       ├── main/java/com/clinic/legacy/    # 7 source files
│       └── test/java/com/clinic/legacy/    # JUnit 5 test suite (5 tests)
├── state/                           # shared coordination directory
│   ├── 00-lock.json                 # pipeline flags
│   ├── dependency-map.json          # Cartographer output
│   ├── architecture-summary.md
│   ├── changelog.md                 # Modernizer output + self-healing loop log
│   ├── build-log.txt                # latest mvn test run output
│   ├── compliance-report.json       # Compliance Officer output
│   └── pr-draft.md                  # Agent mode final output
├── outputs/                         # v1 artifacts (kept for reference)
└── dashboard/
    └── index.html                   # static viewer — reads state/
```

---

## Compliance Rule Set

| Rule ID | Standard | What was checked |
|---|---|---|
| SEC-001 | General secure coding | Hardcoded credentials, API keys, secrets in source |
| GDPR-032 | GDPR Art. 32 | Personal data (SSN, DOB) stored/transmitted without encryption |
| GDPR-005 | GDPR Art. 5 | Full personal records logged unnecessarily (data minimization) |
| HIPAA-164 | HIPAA §164.312 | PHI fields not encrypted or access-controlled |
| SEC-002 | OWASP | Insecure/broken crypto usage — covers unsafe usage patterns, not just broken algorithms |

---

## Hackathon

- **Challenge:** AI Builders Challenge with IBM Bob (BeMyApp / IBM SkillsBuild)
- **Track:** Wildcard — "Build Intelligent Systems for the Future of Work"
- **Deadline:** July 31, 2026
