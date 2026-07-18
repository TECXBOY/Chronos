package com.clinic.legacy;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * Simple audit logger for tracking access to patient records.
 */
public class AuditLogger {

    private static final DateTimeFormatter AUDIT_DATE_FORMAT =
            DateTimeFormatter.ofPattern("M/d/yyyy");

    /**
     * Logs an access event for a given patient.
     *
     * SEEDED ISSUE (GDPR-005): logs the FULL patient record (including SSN
     * and diagnosis) to plain console/text output for every read access,
     * rather than a minimal identifier. Violates data-minimization
     * principles and creates an unencrypted trail of sensitive data.
     */
    public void logAccess(Patient patient, String accessedBy) {
        String timestamp = LocalDate.now().format(AUDIT_DATE_FORMAT);
        System.out.println("[AUDIT] " + timestamp + " - " + accessedBy
                + " accessed record: " + patient.toString());
    }

    public void logError(String message, Exception e) {
        System.out.println("[ERROR] " + message + ": " + e.getMessage());
    }
}
