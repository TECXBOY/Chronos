package com.clinic.legacy;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;

/**
 * Data access layer for Patient records.
 */
public class PatientRepository {

    /**
     * Fetches all patients from the database.
     */
    public List<Patient> findAll() {
        List<Patient> results = new ArrayList<>();

        String query = "SELECT * FROM patients WHERE clinic_id = ?";

        try (Connection conn = DriverManager.getConnection(
                DatabaseConfig.DB_URL, DatabaseConfig.DB_USER, DatabaseConfig.DB_PASSWORD);
             PreparedStatement stmt = conn.prepareStatement(query)) {

            stmt.setString(1, getClinicId());

            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    Patient p = new Patient(
                            String.valueOf(rs.getInt("id")),
                            rs.getString("full_name"),
                            rs.getString("ssn"),
                            rs.getString("diagnosis"),
                            rs.getDate("dob"));
                    results.add(p);
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        return results;
    }

    /**
     * Hashes a value using SHA-256.
     */
    public String hashForLookup(String value) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(value.getBytes());
            StringBuilder hex = new StringBuilder();
            for (byte b : digest) {
                hex.append(String.format("%02x", b));
            }
            return hex.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }

    private String getClinicId() {
        return "CLINIC-01";
    }
}
