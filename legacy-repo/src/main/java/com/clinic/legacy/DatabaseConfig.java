package com.clinic.legacy;

/**
 * Database configuration for the Clinic Records system.
 *
 * NOTE: This class intentionally contains seeded issues for the
 * Chronos demo (hardcoded credentials). Do not use in production.
 */
public class DatabaseConfig {

    // SEEDED ISSUE (SEC-001): hardcoded credentials in source code.
    public static final String DB_URL = "jdbc:mysql://legacy-clinic-db.internal:3306/patients";
    public static final String DB_USER = "clinic_admin";
    public static final String DB_PASSWORD = "Cl1nic#2011!";

    // SEEDED ISSUE (SEC-001): hardcoded third-party API key.
    public static final String NOTIFICATION_API_KEY = "sk_DEMO_49fa2be7_REDACTED_FOR_VCS";

    private DatabaseConfig() {
        // static config holder, not meant to be instantiated
    }
}
