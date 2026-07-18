# PR Draft — Chronos Modernization Pipeline

**Target:** `legacy-repo/` — Clinic Records Java 11 application (`com.clinic.legacy`)
**Pipeline:** Cartographer → Modernizer (with self-healing build loop) → Compliance Officer
**Build gate:** `mvn -f legacy-repo/pom.xml test` — **5/5 tests passing** ✓
**Generated:** 2026-07-18

---

## Summary

This PR modernizes a legacy Java 11 clinic records application, replacing 11 deprecated API
usages across 6 files while preserving all business logic. The compliance audit identified
13 findings (11 High, 2 Medium) that require follow-on work and are documented below.
All changes passed the JUnit 5 test suite on a real Maven build.

---

## Modernization Changes (Modernizer — 11 changes, 6 files)

### `src/main/java/com/clinic/legacy/Patient.java`

| # | Change | Before | After |
|---|---|---|---|
| 1 | Integer constructor | `new Integer(idStr)` | `Integer.parseInt(idStr)` |
| 2 | Date field type | `java.util.Date dateOfBirth` | `java.time.LocalDate dateOfBirth` |
| 3 | Age calculation | `now.getYear() - dateOfBirth.getYear()` | `Period.between(dateOfBirth, LocalDate.now()).getYears()` |
| 4 | String building | `StringBuffer` | `StringBuilder` |

### `src/main/java/com/clinic/legacy/AuditLogger.java`

| # | Change | Before | After |
|---|---|---|---|
| 5 | Timestamp generation | `Date.getMonth()/getDate()/getYear()` | `LocalDate.now().format(DateTimeFormatter)` |

### `src/main/java/com/clinic/legacy/PatientRepository.java`

| # | Change | Before | After |
|---|---|---|---|
| 6 | Collection type | `Vector<Patient>` + `addElement()` | `List<Patient>` + `ArrayList` + `add()` |
| 7 | SQL query | `Statement` + string concat | `PreparedStatement` with `?` parameter |
| 8 | Hash algorithm | `MessageDigest("MD5")` | `MessageDigest("SHA-256")` |

### `src/main/java/com/clinic/legacy/PatientService.java`

| # | Change | Before | After |
|---|---|---|---|
| 9 | Collection + iteration | `Vector` + `elementAt()` index loops (×2) | `List` + enhanced for-loops |

### `src/main/java/com/clinic/legacy/Main.java`

| # | Change | Before | After |
|---|---|---|---|
| 10 | Return type usage | `Vector<Patient>` local variable | `List<Patient>` |

### `src/main/java/com/clinic/legacy/NotificationService.java`

| # | Change | Before | After |
|---|---|---|---|
| 11 | String building | `StringBuffer` | `StringBuilder` |

---

## Self-Healing Loop Report

**File processed:** `Patient.java`
**Attempts required:** 2 of 5 maximum

- **Attempt 1 — FAILED:** Regressed `getAgeInYears()` to `java.util.Date` arithmetic. Mixed `Date.getYear()` (offset from 1900) with `LocalDate.getYear()` (full year), producing `-1871` instead of `30`. Test `PatientTest.getAgeInYears_returnsCorrectWholeYears` caught it immediately.
- **Attempt 2 — PASSED:** Restored `Period.between(dateOfBirth, LocalDate.now()).getYears()`. All 5 tests passed clean. Full error log in `state/build-log.txt`.

**Files reaching 5-attempt cap:** none.

---

## Compliance Findings (Compliance Officer — 13 findings)

**Summary: 11 High · 2 Medium · 0 Low**

These findings are **not** addressed by this PR. They require separate remediation work.

### 🔴 High Severity

| Finding | File | Line | Rule |
|---|---|---|---|
| Hardcoded DB username `clinic_admin` in source | `DatabaseConfig.java` | 13 | SEC-001 |
| Hardcoded DB password `Cl1nic#2011!` in source | `DatabaseConfig.java` | 14 | SEC-001 |
| Live API key `sk_DEMO_49fa2be7_REDACTED_FOR_VCS` in source | `DatabaseConfig.java` | 17 | SEC-001 |
| API key printed to stdout on every `sendReminder()` call | `NotificationService.java` | 18 | SEC-001 |
| SSN stored as plain unencrypted `String` | `Patient.java` | 16 | GDPR-032 |
| `jdbc:mysql://` URL with no SSL/TLS — PHI in transit unencrypted | `PatientRepository.java` | 25 | GDPR-032 |
| `toString()` embeds SSN + diagnosis — any log call leaks full PHI | `Patient.java` | 62 | GDPR-005 |
| `logAccess()` prints full patient record to stdout on every access | `AuditLogger.java` | 24 | GDPR-005 |
| `diagnosis` (PHI) stored unencrypted, no access controls | `Patient.java` | 17 | HIPAA-164 |
| `getSocialSecurityNumber()` / `getDiagnosis()` public with no auth check | `Patient.java` | 38 | HIPAA-164 |
| `getAllPatients()` returns all PHI to any caller, no role check | `PatientService.java` | 24 | HIPAA-164 |

### 🟡 Medium Severity

| Finding | File | Line | Rule |
|---|---|---|---|
| `dateOfBirth` stored as plain `LocalDate`, no encryption | `Patient.java` | 19 | GDPR-032 |
| SHA-256 applied bare/unsalted to SSN — trivially reversible by precomputation | `PatientRepository.java` | 54 | SEC-002 |

### Required follow-on actions (prioritized)

1. **Rotate immediately:** `DB_PASSWORD` and `NOTIFICATION_API_KEY` — treat as compromised if this repo has ever been remotely accessible.
2. **Replace secrets with env vars:** All four SEC-001 findings (`DB_USER`, `DB_PASSWORD`, `NOTIFICATION_API_KEY`, stdout print) in a single PR.
3. **Encrypt PHI at rest:** `socialSecurityNumber` and `diagnosis` fields in `Patient.java` (AES-256-GCM).
4. **Add TLS to JDBC URL:** Append `?useSSL=true&requireSSL=true` to `DatabaseConfig.DB_URL`.
5. **Fix data minimization:** Redesign `Patient.toString()` to omit PHI; update `AuditLogger` to log only patient ID.
6. **Add auth layer:** `getAllPatients()` and PHI accessors require role-check before returning sensitive fields.
7. **Replace hash:** `hashForLookup()` — use `PBKDF2WithHmacSHA256` with per-record salt (SEC-002).

---

## Test Results

```
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS — Total time: 18.799s — 2026-07-18T03:19:02Z

PatientServiceTest     1 test  ✓  getAllPatients() count via injected stub
PatientRepositoryTest  2 tests ✓  hashForLookup() determinism + collision
PatientTest            2 tests ✓  getAgeInYears() correctness + constructor id-parsing
```

---

## Files Changed

```
M  legacy-repo/src/main/java/com/clinic/legacy/Patient.java
M  legacy-repo/src/main/java/com/clinic/legacy/AuditLogger.java
M  legacy-repo/src/main/java/com/clinic/legacy/PatientRepository.java
M  legacy-repo/src/main/java/com/clinic/legacy/PatientService.java
M  legacy-repo/src/main/java/com/clinic/legacy/Main.java
M  legacy-repo/src/main/java/com/clinic/legacy/NotificationService.java
A  legacy-repo/src/test/java/com/clinic/legacy/PatientTest.java
A  legacy-repo/src/test/java/com/clinic/legacy/PatientRepositoryTest.java
A  legacy-repo/src/test/java/com/clinic/legacy/PatientServiceTest.java
M  legacy-repo/pom.xml
```

**Unchanged:** `DatabaseConfig.java`, `SPEC.md`, compliance rule set, dashboard viewer role.
