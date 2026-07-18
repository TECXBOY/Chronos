package com.clinic.legacy;

/**
 * Sends notifications to patients (e.g., appointment reminders) via a
 * third-party notification provider.
 */
public class NotificationService {

    /**
     * Sends a reminder notification for the given patient.
     *
     * SEEDED ISSUE (SEC-001): reuses the hardcoded API key from
     * DatabaseConfig instead of loading it from a secret manager or
     * environment variable.
     */
    public void sendReminder(Patient patient) {
        String payload = buildPayload(patient);
        System.out.println("Sending notification via provider using key: "
                + DatabaseConfig.NOTIFICATION_API_KEY);
        System.out.println("Payload: " + payload);
        // In a real system this would call out to an HTTP client / SDK.
    }

    private String buildPayload(Patient patient) {
        // SEEDED ISSUE (Modernizer target): StringBuffer used where
        // StringBuilder (non-synchronized, faster) is the modern default
        // for single-threaded string building.
        StringBuilder sb = new StringBuilder();
        sb.append("Hello ").append(patient.getFullName())
          .append(", this is a reminder about your upcoming appointment.");
        return sb.toString();
    }
}
