"""
Entry point for the Clinic Records legacy application.

LEGACY patterns present in this file:
  - print statement (Python 2)
  - xrange() instead of range()
  - dict.iteritems() instead of .items()
"""
from clinic.patient_repository import PatientRepository
from clinic.audit_logger import AuditLogger
from clinic.notification_service import NotificationService


def main():
    repo = PatientRepository()
    logger = AuditLogger()
    notifier = NotificationService()

    # LEGACY: print statement — SyntaxError in Python 3.
    print "=== Clinic Records System starting up ==="

    patients = repo.find_all()

    # LEGACY: xrange() — NameError in Python 3 (xrange was removed).
    # Modernizer target: replace with range()
    for i in xrange(len(patients)):
        logger.log_access(patients[i], "system-startup")

    # LEGACY: dict.iteritems() — AttributeError in Python 3.
    # Modernizer target: replace with .items()
    summary = {"processed": len(patients), "errors": 0}
    for key, val in summary.iteritems():
        print "  %s: %s" % (key, val)

    # Send reminders
    for patient in patients:
        notifier.send_reminder(patient)

    print "=== Startup complete ==="


if __name__ == "__main__":
    main()
