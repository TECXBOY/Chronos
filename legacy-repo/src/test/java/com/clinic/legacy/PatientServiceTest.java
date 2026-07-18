package com.clinic.legacy;

import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class PatientServiceTest {

    @Test
    void getAllPatients_returnsSameCountAsRepository() {
        // Build two well-formed Patient objects for the stub to return.
        Patient p1 = new Patient("1", "Alice Smith",  "111-11-1111", "hypertension",
                java.sql.Date.valueOf(LocalDate.now().minusYears(40)));
        Patient p2 = new Patient("2", "Bob Jones",    "222-22-2222", "diabetes",
                java.sql.Date.valueOf(LocalDate.now().minusYears(55)));

        // Anonymous stub — overrides only findAll(), never touches JDBC.
        PatientRepository stubRepo = new PatientRepository() {
            @Override
            public List<Patient> findAll() {
                return List.of(p1, p2);
            }
        };

        // No-op stubs for the collaborators PatientService calls on each patient.
        AuditLogger stubLogger = new AuditLogger() {
            @Override public void logAccess(Patient patient, String accessedBy) { /* no-op */ }
        };
        NotificationService stubNotifier = new NotificationService() {
            @Override public void sendReminder(Patient patient) { /* no-op */ }
        };

        PatientService service = new PatientService(stubRepo, stubLogger, stubNotifier);

        List<Patient> result = service.getAllPatients("test-runner");
        assertEquals(2, result.size(),
                "getAllPatients() should return exactly as many records as the repository provides");
    }
}
