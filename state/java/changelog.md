## src/main/java/com/clinic/legacy/Patient.java

**Change 1 — Replace deprecated java.util.Date with java.time.LocalDate**
**Before:**
```java
import java.util.Date;
private Date dateOfBirth;
public Patient(String idStr, String fullName, String ssn, String diagnosis, Date dateOfBirth) {
    this.dateOfBirth = dateOfBirth;
}
public int getAgeInYears() {
    Date now = new Date();
    int age = now.getYear() - dateOfBirth.getYear() - 1;
    return age;
}
```
**After:**
```java
import java.time.LocalDate;
import java.time.Period;
private LocalDate dateOfBirth;
public Patient(String idStr, String fullName, String ssn, String diagnosis, java.sql.Date dateOfBirth) {
    this.dateOfBirth = dateOfBirth.toLocalDate();
}
public int getAgeInYears() {
    return Period.between(dateOfBirth, LocalDate.now()).getYears();
}
```
**Reason:** java.util.Date is deprecated; java.time.Period.between() correctly computes completed years across month/day boundaries without the getYear()+1900 offset bug that caused age=-1871 in self-healing attempt 1.

---

**Change 2 — Replace new Integer(String) constructor with Integer.parseInt()**
**Before:**
```java
this.id = new Integer(idStr);
```
**After:**
```java
this.id = Integer.parseInt(idStr);
```
**Reason:** Integer(String) constructor is deprecated since Java 9; Integer.parseInt() is the canonical replacement and has identical semantics for valid numeric strings.

---

**Change 3 — Replace StringBuffer with StringBuilder in toString()**
**Before:**
```java
StringBuffer sb = new StringBuffer();
sb.append("Patient{id=").append(id) ...
```
**After:**
```java
StringBuilder sb = new StringBuilder();
sb.append("Patient{id=").append(id) ...
```
**Reason:** StringBuffer is synchronized and deprecated for single-threaded use; StringBuilder is the non-synchronized replacement with identical API and better performance.

---

## src/main/java/com/clinic/legacy/PatientRepository.java

**Change 1 — Replace java.sql.Statement (raw concat) with PreparedStatement**
**Before:**
```java
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery("SELECT * FROM patients WHERE id = " + id);
```
**After:**
```java
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM patients WHERE id = ?");
stmt.setInt(1, id);
ResultSet rs = stmt.executeQuery();
```
**Reason:** Raw string concatenation into Statement is a SQL injection vector; PreparedStatement with parameterised queries eliminates the injection risk and is the modern JDBC pattern.

---

**Change 2 — Replace MessageDigest MD5 with SHA-256 in hashForLookup()**
**Before:**
```java
MessageDigest md = MessageDigest.getInstance("MD5");
byte[] digest = md.digest(value.getBytes(StandardCharsets.UTF_8));
StringBuilder hex = new StringBuilder();
for (byte b : digest) {
    hex.append(String.format("%02x", b));
}
return hex.toString();
```
**After:**
```java
MessageDigest md = MessageDigest.getInstance("SHA-256");
byte[] digest = md.digest(value.getBytes(StandardCharsets.UTF_8));
StringBuilder hex = new StringBuilder();
for (byte b : digest) {
    hex.append(String.format("%02x", b));
}
return hex.toString();
```
**Reason:** MD5 is cryptographically broken and flagged by SEC-002; SHA-256 is the minimum acceptable replacement. Note: bare unsalted hashing of SSNs remains a SEC-002 finding for the Compliance Officer — Modernizer upgrades the algorithm only.

---

## src/main/java/com/clinic/legacy/PatientService.java

**Change 1 — Replace Vector with ArrayList**
**Before:**
```java
import java.util.Vector;
Vector<Patient> results = new Vector<>();
results.addElement(p);
```
**After:**
```java
import java.util.ArrayList;
import java.util.List;
List<Patient> results = new ArrayList<>();
results.add(p);
```
**Reason:** Vector is a legacy synchronized collection deprecated for single-threaded use; ArrayList with the List interface is the standard replacement.

---

## src/main/java/com/clinic/legacy/AuditLogger.java

**Change 1 — Replace StringBuffer with StringBuilder**
**Before:**
```java
StringBuffer sb = new StringBuffer();
sb.append("[AUDIT] ").append(timestamp).append(" | ").append(patient.toString());
```
**After:**
```java
StringBuilder sb = new StringBuilder();
sb.append("[AUDIT] ").append(timestamp).append(" | ").append(patient.toString());
```
**Reason:** StringBuffer is synchronized and deprecated for single-threaded use; StringBuilder is the non-synchronized replacement.

---
