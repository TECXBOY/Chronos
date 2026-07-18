package com.clinic.legacy;

import org.junit.jupiter.api.Test;

import java.time.LocalDate;

import static org.junit.jupiter.api.Assertions.assertEquals;

class PatientTest {

    private static Patient makePatient(String idStr, LocalDate dob) {
        return new Patient(
                idStr,
                "Test Patient",
                "000-00-0000",
                "none",
                java.sql.Date.valueOf(dob));
    }

    @Test
    void getAgeInYears_returnsCorrectWholeYears() {
        // DOB is computed dynamically so this test stays correct on any run date.
        LocalDate dob = LocalDate.now().minusYears(30);
        Patient patient = makePatient("1", dob);
        assertEquals(30, patient.getAgeInYears(),
                "getAgeInYears() should return 30 for a patient born exactly 30 years ago");
    }

    @Test
    void constructor_parsesIdStringToInteger() {
        Patient patient = makePatient("42", LocalDate.now().minusYears(25));
        assertEquals(42, patient.getId(),
                "constructor should parse the id string '42' to Integer 42");
    }
}
