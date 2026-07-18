package com.clinic.legacy;

import java.util.List;

/**
 * Entry point for the legacy Clinic Records application.
 */
public class Main {

    public static void main(String[] args) {
        PatientService patientService = new PatientService();

        List<Patient> patients = patientService.getAllPatients("system-startup");
        System.out.println("Loaded " + patients.size() + " patient records.");

        patientService.sendAllReminders();

        System.out.println("Clinic Records legacy application finished startup routine.");
    }
}
