"""
Tests for PatientRepository.hash_for_lookup().

Equivalent Java tests:
  - PatientRepositoryTest.hashForLookup_isDeterministic
  - PatientRepositoryTest.hashForLookup_producesDifferentOutputForDifferentInput

NOTE: PatientRepository.find_all() requires a live database connection and
cannot be unit-tested here — same constraint as the Java suite.
Only hash_for_lookup() is a pure function and is safe to test in isolation.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from clinic.patient_repository import PatientRepository


def test_hash_for_lookup_is_deterministic():
    """
    Calling hash_for_lookup() twice with the same input must return the same value.
    Mirrors: PatientRepositoryTest.hashForLookup_isDeterministic
    """
    repo = PatientRepository()
    ssn = "123-45-6789"
    first = repo.hash_for_lookup(ssn)
    second = repo.hash_for_lookup(ssn)
    assert first == second, (
        "hash_for_lookup() must return the same value for the same input on repeated calls"
    )


def test_hash_for_lookup_differs_for_different_inputs():
    """
    Two distinct SSNs must produce two distinct hash values.
    An empty-loop or constant-return regression would produce "" == "" and fail here.
    Mirrors: PatientRepositoryTest.hashForLookup_producesDifferentOutputForDifferentInput
    """
    repo = PatientRepository()
    hash1 = repo.hash_for_lookup("123-45-6789")
    hash2 = repo.hash_for_lookup("987-65-4321")
    assert hash1 != hash2, (
        "hash_for_lookup() must return distinct values for distinct inputs"
    )
