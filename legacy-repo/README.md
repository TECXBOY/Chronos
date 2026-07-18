# Clinic Records — Legacy Demo Application

This is a small, intentionally-flawed Java 11 codebase used as the demo
target for **Chronos**. It simulates a real-world clinic/patient records
system with the kind of technical debt and compliance gaps Chronos is
designed to find and fix.

**Do not use this code in production. It is seeded with issues on purpose.**

## Structure

```
src/main/java/com/clinic/legacy/
├── Main.java                # entry point
├── PatientService.java      # business logic, orchestrates the rest
├── PatientRepository.java   # data access layer
├── Patient.java             # domain model
├── DatabaseConfig.java      # static config (hardcoded secrets)
├── NotificationService.java # third-party notification integration
└── AuditLogger.java         # access logging
```

Dependency chain (for the Cartographer to discover):
`Main → PatientService → {PatientRepository, AuditLogger, NotificationService}`
`PatientRepository → DatabaseConfig`
`NotificationService → DatabaseConfig`
`PatientService / AuditLogger → Patient`

## Seeded Issues Index

### Modernization targets (deprecated / legacy patterns)
| # | File | Issue |
|---|---|---|
| 1 | `Patient.java` | `new Integer(String)` constructor — deprecated since Java 9 |
| 2 | `Patient.java` | `Date#getYear()` / legacy `Date` usage — deprecated since JDK 1.1 |
| 3 | `AuditLogger.java` | `Date#getMonth()` / `Date#getDate()` — deprecated since JDK 1.1 |
| 4 | `PatientRepository.java` | `java.util.Vector` used instead of `ArrayList`/`List` |
| 5 | `PatientService.java` | `java.util.Vector` used instead of `ArrayList`/`List` |
| 6 | `Patient.java`, `NotificationService.java`, `PatientRepository.java` | `StringBuffer` used instead of `StringBuilder` |

### Compliance / security findings (for the Compliance Officer)
| # | File | Rule | Issue |
|---|---|---|---|
| 1 | `DatabaseConfig.java` | SEC-001 | Hardcoded DB credentials |
| 2 | `DatabaseConfig.java` | SEC-001 | Hardcoded third-party API key |
| 3 | `Patient.java` | GDPR-032 / HIPAA-164 | SSN and diagnosis stored as plain unencrypted `String` |
| 4 | `Patient.java`, `AuditLogger.java` | GDPR-005 | Full PHI (SSN + diagnosis) concatenated and logged on every access |
| 5 | `PatientRepository.java` | SEC-002 | MD5 used for hashing (broken algorithm) |
| 6 | `PatientRepository.java` | SEC-002 | Raw SQL string concatenation — SQL injection risk |

This index is for internal reference. It should **not** be shown to the
Cartographer/Modernizer/Compliance Officer agents directly — the point of
the demo is that Bob's agents find these independently.
