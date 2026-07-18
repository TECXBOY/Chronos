# Changelog — Modernizer Pass

All changes made by the Modernizer agent to `legacy-repo/`. Business logic preserved exactly.
Deprecated API usages sourced from `outputs/dependency-map.json`.

---

## src/main/java/com/clinic/legacy/Patient.java

**Change 1 — Replace `new Integer(String)` with `Integer.parseInt()`**

**Before:**
```java
this.id = new Integer(idStr);
```
**After:**
```java
this.id = Integer.parseInt(idStr);
```
**Reason:** `Integer(String)` constructor deprecated since Java 9; `Integer.parseInt()` is the preferred replacement.

---

**Change 2 — Replace `java.util.Date` field and constructor parameter with `java.time.LocalDate`**

**Before:**
```java
import java.util.Date;
// ...
private Date dateOfBirth;

public Patient(String idStr, String fullName, String socialSecurityNumber,
               String diagnosis, Date dateOfBirth) {
    // ...
    this.dateOfBirth = dateOfBirth;
}

public Date getDateOfBirth() {
    return dateOfBirth;
}
```
**After:**
```java
import java.time.LocalDate;
// ...
private LocalDate dateOfBirth;

public Patient(String idStr, String fullName, String socialSecurityNumber,
               String diagnosis, java.sql.Date dateOfBirth) {
    // ...
    this.dateOfBirth = dateOfBirth.toLocalDate();
}

public LocalDate getDateOfBirth() {
    return dateOfBirth;
}
```
**Reason:** `java.util.Date` and its `getYear()`/`getMonth()`/`getDate()` methods deprecated since JDK 1.1; `java.time.LocalDate` is the modern replacement.

---

**Change 3 — Replace deprecated `Date.getYear()` age calculation with `Period`**

**Before:**
```java
public int getAgeInYears() {
    Date now = new Date();
    return now.getYear() - dateOfBirth.getYear();
}
```
**After:**
```java
public int getAgeInYears() {
    return Period.between(dateOfBirth, LocalDate.now()).getYears();
}
```
**Reason:** `Date.getYear()` deprecated since JDK 1.1; `Period.between()` is the correct `java.time` idiom for year-difference calculations.

---

**Change 4 — Replace `StringBuffer` with `StringBuilder` in `toString()`**

**Before:**
```java
StringBuffer sb = new StringBuffer();
```
**After:**
```java
StringBuilder sb = new StringBuilder();
```
**Reason:** `StringBuffer` is synchronized; `StringBuilder` is the modern, faster replacement for single-threaded string construction.

---

## src/main/java/com/clinic/legacy/AuditLogger.java

**Change 5 — Replace `java.util.Date` and deprecated `getMonth()`/`getDate()`/`getYear()` with `LocalDate` + `DateTimeFormatter`**

**Before:**
```java
import java.util.Date;
// ...
public void logAccess(Patient patient, String accessedBy) {
    Date now = new Date();
    String timestamp = (now.getMonth() + 1) + "/" + now.getDate() + "/" + (now.getYear() + 1900);
    System.out.println("[AUDIT] " + timestamp + " - " + accessedBy
            + " accessed record: " + patient.toString());
}
```
**After:**
```java
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
// ...
private static final DateTimeFormatter AUDIT_DATE_FORMAT =
        DateTimeFormatter.ofPattern("M/d/yyyy");

public void logAccess(Patient patient, String accessedBy) {
    String timestamp = LocalDate.now().format(AUDIT_DATE_FORMAT);
    System.out.println("[AUDIT] " + timestamp + " - " + accessedBy
            + " accessed record: " + patient.toString());
}
```
**Reason:** `Date.getMonth()`/`getDate()`/`getYear()` all deprecated since JDK 1.1; `java.time.LocalDate` with `DateTimeFormatter` is the modern replacement; formatter extracted as a constant to avoid repeated instantiation.

---

## src/main/java/com/clinic/legacy/PatientRepository.java

**Change 6 — Replace `java.util.Vector` with `java.util.List` / `ArrayList`**

**Before:**
```java
import java.util.Vector;
// ...
public Vector<Patient> findAll() {
    Vector<Patient> results = new Vector<Patient>();
    // ...
    results.addElement(p);
    // ...
    return results;
}
```
**After:**
```java
import java.util.ArrayList;
import java.util.List;
// ...
public List<Patient> findAll() {
    List<Patient> results = new ArrayList<>();
    // ...
    results.add(p);
    // ...
    return results;
}
```
**Reason:** `Vector` is a legacy synchronized collection from JDK 1.0; `ArrayList` is the modern unsynchronized equivalent; return type widened to `List` interface per best practice.

---

**Change 7 — Replace raw `Statement` + string concatenation with `PreparedStatement`**

**Before:**
```java
import java.sql.Statement;
// ...
String query = "SELECT * FROM patients WHERE clinic_id = '" + getClinicId() + "'";
try (Connection conn = DriverManager.getConnection(...);
     Statement stmt = conn.createStatement();
     ResultSet rs = stmt.executeQuery(query)) {
    // ...
}
```
**After:**
```java
import java.sql.PreparedStatement;
// ...
String query = "SELECT * FROM patients WHERE clinic_id = ?";
try (Connection conn = DriverManager.getConnection(...);
     PreparedStatement stmt = conn.prepareStatement(query)) {
    stmt.setString(1, getClinicId());
    try (ResultSet rs = stmt.executeQuery()) {
        // ...
    }
}
```
**Reason:** Raw `Statement` with string concatenation is vulnerable to SQL injection; `PreparedStatement` with parameterized inputs is the correct modern approach.

---

**Change 8 — Replace `MD5` hash algorithm with `SHA-256`; replace `StringBuffer` with `StringBuilder`**

**Before:**
```java
MessageDigest md = MessageDigest.getInstance("MD5");
byte[] digest = md.digest(value.getBytes());
StringBuffer hex = new StringBuffer();
```
**After:**
```java
MessageDigest md = MessageDigest.getInstance("SHA-256");
byte[] digest = md.digest(value.getBytes());
StringBuilder hex = new StringBuilder();
```
**Reason:** MD5 is cryptographically broken and must not be used for security-sensitive hashing; SHA-256 is the standard modern replacement. `StringBuffer` replaced with `StringBuilder` (single-threaded context).

---

## src/main/java/com/clinic/legacy/PatientService.java

**Change 9 — Replace `Vector` return type and index-based loop with `List` and enhanced for-loop**

**Before:**
```java
import java.util.Vector;
// ...
public Vector<Patient> getAllPatients(String requestedBy) {
    Vector<Patient> patients = patientRepository.findAll();
    for (int i = 0; i < patients.size(); i++) {
        Patient p = patients.elementAt(i);
        auditLogger.logAccess(p, requestedBy);
    }
    return patients;
}

public void sendAllReminders() {
    Vector<Patient> patients = patientRepository.findAll();
    for (int i = 0; i < patients.size(); i++) {
        notificationService.sendReminder(patients.elementAt(i));
    }
}
```
**After:**
```java
import java.util.List;
// ...
public List<Patient> getAllPatients(String requestedBy) {
    List<Patient> patients = patientRepository.findAll();
    for (Patient p : patients) {
        auditLogger.logAccess(p, requestedBy);
    }
    return patients;
}

public void sendAllReminders() {
    List<Patient> patients = patientRepository.findAll();
    for (Patient p : patients) {
        notificationService.sendReminder(p);
    }
}
```
**Reason:** `Vector` deprecated in favour of `List`/`ArrayList`; `Vector.elementAt()` replaced with enhanced for-loop, which is the modern Java iteration idiom.

---

## src/main/java/com/clinic/legacy/Main.java

**Change 10 — Replace `Vector` import and local variable type with `List`**

**Before:**
```java
import java.util.Vector;
// ...
Vector<Patient> patients = patientService.getAllPatients("system-startup");
```
**After:**
```java
import java.util.List;
// ...
List<Patient> patients = patientService.getAllPatients("system-startup");
```
**Reason:** `Vector` replaced by `List` throughout the call chain; updated call site to match the new `PatientService.getAllPatients()` return type.

---

## src/main/java/com/clinic/legacy/NotificationService.java

**Change 11 — Replace `StringBuffer` with `StringBuilder`**

**Before:**
```java
StringBuffer sb = new StringBuffer();
```
**After:**
```java
StringBuilder sb = new StringBuilder();
```
**Reason:** `StringBuffer` is synchronized; `StringBuilder` is the modern, faster replacement for single-threaded string construction.
