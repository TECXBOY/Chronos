package com.clinic.legacy;

import java.time.LocalDate;
import java.time.Period;

/**
 * Represents a patient record in the clinic system.
 */
public class Patient {

    private Integer id;
    private String fullName;

    // SEEDED ISSUE (GDPR-032 / HIPAA-164): sensitive personal and health data
    // stored as plain, unencrypted String fields.
    private String socialSecurityNumber;
    private String diagnosis;

    private LocalDate dateOfBirth;

    public Patient(String idStr, String fullName, String socialSecurityNumber,
                   String diagnosis, java.sql.Date dateOfBirth) {
        this.id = Integer.parseInt(idStr);
        this.fullName = fullName;
        this.socialSecurityNumber = socialSecurityNumber;
        this.diagnosis = diagnosis;
        this.dateOfBirth = dateOfBirth.toLocalDate();
    }

    public Integer getId() {
        return id;
    }

    public String getFullName() {
        return fullName;
    }

    public String getSocialSecurityNumber() {
        return socialSecurityNumber;
    }

    public String getDiagnosis() {
        return diagnosis;
    }

    public LocalDate getDateOfBirth() {
        return dateOfBirth;
    }

    /**
     * Returns the patient's age in whole years.
     */
    public int getAgeInYears() {
        return Period.between(dateOfBirth, LocalDate.now()).getYears();
    }

    @Override
    public String toString() {
        // SEEDED ISSUE (GDPR-005): full PHI concatenated into a plain string,
        // encourages data-minimization violations wherever this is logged.
        StringBuilder sb = new StringBuilder();
        sb.append("Patient{id=").append(id)
          .append(", name=").append(fullName)
          .append(", ssn=").append(socialSecurityNumber)
          .append(", diagnosis=").append(diagnosis)
          .append("}");
        return sb.toString();
    }
}
