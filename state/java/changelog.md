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

