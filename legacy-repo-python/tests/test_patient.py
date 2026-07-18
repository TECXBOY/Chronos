"""
Tests for the Patient domain model.

Equivalent Java tests:
  - PatientTest.getAgeInYears_returnsCorrectWholeYears
  - PatientTest.constructor_parsesIdStringToInteger
"""
import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from clinic.patient import Patient


def _make_patient(patient_id, dob):
    """Helper: create a Patient with minimal required fields."""
    return Patient(
        patient_id,
        "Test Patient",
        "000-00-0000",
        "none",
        dob,
    )


def test_get_age_in_years_returns_correct_whole_years():
    """
    A patient born exactly 30 years ago today should have age == 30.

    Uses date arithmetic (the modernized form). The legacy implementation
    used implicit integer division which produced wrong results in Python 2
    and is non-obvious — this test would catch a regression back to that form.
    DOB is computed dynamically so this test stays correct on any run date.
    """
    dob = datetime.date.today().replace(year=datetime.date.today().year - 30)
    patient = _make_patient("1", dob)
    assert patient.get_age_in_years() == 30, (
        "get_age_in_years() should return 30 for a patient born exactly 30 years ago"
    )


def test_patient_id_is_stored_as_integer():
    """
    The constructor accepts a string ID and must store it as int.
    Mirrors: PatientTest.constructor_parsesIdStringToInteger
    """
    dob = datetime.date.today().replace(year=datetime.date.today().year - 25)
    patient = _make_patient("42", dob)
    assert patient.id == 42, (
        "Patient constructor should parse the string '42' to integer 42"
    )
    assert isinstance(patient.id, int), (
        "patient.id must be an int, not a string"
    )
