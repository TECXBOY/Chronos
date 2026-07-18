package com.clinic.legacy;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;

class PatientRepositoryTest {

    private final PatientRepository repo = new PatientRepository();

    @Test
    void hashForLookup_isDeterministic() {
        String input = "123-45-6789";
        String first  = repo.hashForLookup(input);
        String second = repo.hashForLookup(input);
        assertEquals(first, second,
                "hashForLookup() must return the same value for the same input on repeated calls");
    }

    @Test
    void hashForLookup_producesDifferentOutputForDifferentInput() {
        String hash1 = repo.hashForLookup("123-45-6789");
        String hash2 = repo.hashForLookup("987-65-4321");
        assertNotEquals(hash1, hash2,
                "hashForLookup() must return distinct values for distinct inputs");
    }
}
