## 🤖 Chronos Automated Modernization — Java

**Target:** `legacy-repo/` · Java 11 → modern Java (java.time, StringBuilder, ArrayList, PreparedStatement, SHA-256)
**Build gate:** `mvn test` · 5/5 tests passing ✓
**Pipeline:** Cartographer → Modernizer (self-healing loop) → Compliance Officer
**Branch:** `chronos/modernize-java-20260718T110628Z`
**Generated:** 2026-07-18 by Chronos Modernizer (IBM Bob AI Builders Challenge)

---

## Modernization Changes

# Self-Healing Loop Log — Patient.java

**File:** `src/main/java/com/clinic/legacy/Patient.java`
**Gate command:** `mvn -q -f legacy-repo/pom.xml test`
**Total attempts:** 2
**Final status:** PASSED

---

## Attempt 1 — FAILED

**Change applied:**
Regression introduced to `getAgeInYears()`: replaced `Period.between(dateOfBirth, LocalDate.now()).getYears()` with a `java.util.Date`-based arithmetic implementation:
```java
Date now = new Date();
int age = (now.getYear() + 1900) - (dateOfBirth.getYear() + 1900) - 1;
```

**Build result:** `BUILD FAILURE` — exit code 1

**Test failure:**
```
PatientTest.getAgeInYears_returnsCorrectWholeYears
expected: <30> but was: <-1871>
```

**Diagnosis:** `java.util.Date.getYear()` returns years offset from 1900 (e.g. 126 for 2026), while `LocalDate.getYear()` (used on `dateOfBirth`) returns the full year (e.g. 1996). Adding `+1900` to both compounds the mismatch: `(126 + 1900) - (1996 + 1900) - 1 = 2026 - 3896 - 1 = -1871`. The regression also violates the modernization goal by re-introducing the deprecated `java.util.Date` API. Both errors are in the same method.

**Full error output:** `state/build-log.txt` (run 1)

---

## Attempt 2 — PASSED

**Change applied:**
Restored the correct `java.time` implementation and removed the spurious `java.util.Date` import:
```java
public int getAgeInYears() {
    return Period.between(dateOfBirth, LocalDate.now()).getYears();
}
```

**Reasoning:** `Period.between(start, end).getYears()` correctly computes completed years taking month and day boundaries into account. `Date.getYear()` arithmetic is both deprecated and semantically broken for this use case. The fix restores the modernization goal without any other change.

**Build result:** `BUILD SUCCESS` — exit code 0

```
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS — Total time: 18.799s — 2026-07-18T03:19:02Z
```

**Full output:** `state/build-log.txt` (run 2, appended)

---

# Self-Healing Loop Log — PatientRepository.java (Run 2, 2026-07-18)

**File:** `src/main/java/com/clinic/legacy/PatientRepository.java`
**Gate command:** `mvn -q -f legacy-repo/pom.xml test`
**Total attempts:** 2
**Final status:** PASSED

---

## Attempt 1 — FAILED

**Regression introduced:**
Emptied the `for` loop body in `hashForLookup()` — the `hex` `StringBuilder` is
never populated, so the method returns `""` for every input regardless of value.
This compiles without errors or warnings.

```java
// BEFORE (correct):
for (byte b : digest) {
    hex.append(String.format("%02x", b));
}

// AFTER (regression — loop body removed):
for (byte b : digest) {
    // loop body missing
}
```

**Build result:** `BUILD FAILURE` — exit code 1

**Test failure:**
```
PatientRepositoryTest.hashForLookup_producesDifferentOutputForDifferentInput
expected: not equal but was: <>
```

**Diagnosis from state/build-log.txt:**
The value `<>` (empty string) returned for both inputs proves the hex accumulator
is never written. The `MessageDigest` computes the SHA-256 digest correctly but the
byte-to-hex conversion loop body is missing — `hex.toString()` returns `""` always.
The determinism test passes (two calls to `""` are equal) but the collision test
correctly fails (`"" equals ""`). Fix: restore `hex.append(String.format("%02x", b))`.

**Full log:** `state/build-log.txt` (Attempt 1 section)

---

## Attempt 2 — PASSED

**Fix applied:**
Restored the hex-encoding loop body:

```java
for (byte b : digest) {
    hex.append(String.format("%02x", b));
}
```

**Reasoning:** The `StringBuilder` accumulates two hex characters per byte. With a
32-byte SHA-256 digest the result is a 64-character lowercase hex string. The empty
loop produces `""` regardless of input — a structural logic error that only a
value-checking test can catch at this level of specificity.

**Build result:** `BUILD SUCCESS` — exit code 0

```
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS — 2026-07-18T03:25:26Z
```

**Full log:** `state/build-log.txt` (Attempt 2 section, appended)



---

## ⚠️ Compliance Findings — NOT fixed in this PR

> **These 13 findings require a separate dedicated remediation PR.**
> Do not merge this PR under the assumption that compliance issues are resolved.

**Summary: 11 High · 2 Medium · 0 Low**

| Severity | File | Line | Rule | Description |
|---|---|---|---|---|
| 🔴 High | `src/main/java/com/clinic/legacy/DatabaseConfig.java` | 13 | SEC-001 | Hardcoded database username 'clinic_admin' committed as a public static final String. Any developer or process… |
| 🔴 High | `src/main/java/com/clinic/legacy/DatabaseConfig.java` | 14 | SEC-001 | Hardcoded database password 'Cl1nic#2011!' committed as a public static final String. Exposure via source cont… |
| 🔴 High | `src/main/java/com/clinic/legacy/DatabaseConfig.java` | 17 | SEC-001 | Live third-party notification API key ('sk_live_...') hardcoded as a public static final String. The 'sk_live_… |
| 🔴 High | `src/main/java/com/clinic/legacy/NotificationService.java` | 18 | SEC-001 | The live API key is actively printed to stdout via System.out.println() on every call to sendReminder(). Even … |
| 🔴 High | `src/main/java/com/clinic/legacy/Patient.java` | 16 | GDPR-032 | socialSecurityNumber (SSN) is stored as a plain, unencrypted String field. GDPR Art. 32 requires appropriate t… |
| 🟡 Medium | `src/main/java/com/clinic/legacy/Patient.java` | 19 | GDPR-032 | dateOfBirth is stored as a plain LocalDate field without any encryption or access control. Date of birth is pe… |
| 🔴 High | `src/main/java/com/clinic/legacy/PatientRepository.java` | 25 | GDPR-032 | The JDBC connection URL uses the plaintext 'jdbc:mysql://' scheme with no SSL/TLS parameters. All patient PII … |
| 🔴 High | `src/main/java/com/clinic/legacy/Patient.java` | 62 | GDPR-005 | The toString() method concatenates the full patient record including socialSecurityNumber and diagnosis into a… |
| 🔴 High | `src/main/java/com/clinic/legacy/AuditLogger.java` | 24 | GDPR-005 | logAccess() calls patient.toString() which includes the full SSN and diagnosis, and prints the result to stdou… |
| 🔴 High | `src/main/java/com/clinic/legacy/Patient.java` | 17 | HIPAA-164 | The diagnosis field contains Protected Health Information (PHI) as defined by HIPAA §164.312. It is stored as … |
| 🔴 High | `src/main/java/com/clinic/legacy/Patient.java` | 38 | HIPAA-164 | getSocialSecurityNumber() and getDiagnosis() are public methods with no access control — any object holding a … |
| 🔴 High | `src/main/java/com/clinic/legacy/PatientService.java` | 24 | HIPAA-164 | getAllPatients() returns the complete list of every patient record — including PHI fields — to any caller with… |
| 🟡 Medium | `src/main/java/com/clinic/legacy/PatientRepository.java` | 54 | SEC-002 | SHA-256 is applied as a bare, unsalted hash to SSN values in hashForLookup(). SSNs occupy a small, enumerable … |

---

## ⛔ Draft PR — Human Review Required

- [ ] Review all modernization changes in the diff above
- [ ] Confirm no business logic was altered (only syntax/API upgrades)
- [ ] Open a **separate** remediation PR for the 13 compliance findings above
- [ ] Do not merge without explicit human sign-off

> Full compliance report: `state/java/compliance-report.json`
> Full self-healing loop log: `state/java/build-log.txt`
