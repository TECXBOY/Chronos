package com.clinic.legacy;

import java.util.List;

/**
 * Core business logic for working with patient records.
 * Coordinates the repository, audit logger, and notification service.
 */
public class PatientService {

    private final PatientRepository patientRepository;
    private final AuditLogger auditLogger;
    private final NotificationService notificationService;

    public PatientService() {
        this.patientRepository = new PatientRepository();
        this.auditLogger = new AuditLogger();
        this.notificationService = new NotificationService();
    }

    /** Package-private constructor for testing — allows injecting stubs. */
    PatientService(PatientRepository patientRepository, AuditLogger auditLogger,
                   NotificationService notificationService) {
        this.patientRepository = patientRepository;
        this.auditLogger = auditLogger;
        this.notificationService = notificationService;
    }

    /**
     * Retrieves all patients and logs the access.
     */
    public List<Patient> getAllPatients(String requestedBy) {
        List<Patient> patients = patientRepository.findAll();

        for (Patient p : patients) {
            auditLogger.logAccess(p, requestedBy);
        }

        return patients;
    }

    /**
     * Sends appointment reminders to every patient in the system.
     */
    public void sendAllReminders() {
        List<Patient> patients = patientRepository.findAll();
        for (Patient p : patients) {
            notificationService.sendReminder(p);
        }
    }

    /**
     * Looks up a patient record using a hashed identifier.
     */
    public String buildLookupKey(String ssn) {
        return patientRepository.hashForLookup(ssn);
    }
}
