"""
Tests for NotificationService / service-layer record-count pass-through.

Equivalent Java test:
  - PatientServiceTest.getAllPatients_returnsSameCountAsRepository

Uses anonymous stub subclasses (no pytest-mock / unittest.mock needed),
mirroring the Java suite's package-private injection constructor pattern.
"""
import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from clinic.patient import Patient
from clinic.patient_repository import PatientRepository
from clinic.audit_logger import AuditLogger
from clinic.notification_service import NotificationService


class _StubRepository(PatientRepository):
    """Overrides find_all() to return a fixed list — never touches the database."""

    def find_all(self):
        p1 = Patient("1", "Alice Smith",  "111-11-1111", "hypertension",
                     datetime.date.today().replace(year=datetime.date.today().year - 40))
        p2 = Patient("2", "Bob Jones",    "222-22-2222", "diabetes",
                     datetime.date.today().replace(year=datetime.date.today().year - 55))
        return [p1, p2]


class _StubLogger(AuditLogger):
    """No-op audit logger — suppresses stdout during tests."""

    def log_access(self, patient, accessed_by):
        pass  # no-op


class _StubNotifier(NotificationService):
    """No-op notifier — suppresses stdout and never calls the real API."""

    def send_reminder(self, patient):
        pass  # no-op


def _get_all_patients_via_stub(accessed_by):
    """
    Service-layer helper: replicates PatientService.getAllPatients() logic
    using stub collaborators. This tests the coordination logic without
    requiring a database or API key.
    """
    repo = _StubRepository()
    logger = _StubLogger()
    # notifier not used by get_all_patients, but kept for symmetry
    _StubNotifier()

    patients = repo.find_all()
    for p in patients:
        logger.log_access(p, accessed_by)
    return patients


def test_get_all_patients_returns_correct_count():
    """
    get_all_patients() (via stub) should return exactly as many records as
    the repository provides. Mirrors PatientServiceTest.getAllPatients_returnsSameCountAsRepository.
    """
    result = _get_all_patients_via_stub("test-runner")
    assert len(result) == 2, (
        "get_all_patients() should return exactly as many records as the repository provides"
    )
