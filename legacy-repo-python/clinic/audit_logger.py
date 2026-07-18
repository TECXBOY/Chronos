"""
Access audit logger for the Clinic Records system.
"""
import datetime


class AuditLogger(object):

    def log_access(self, patient, accessed_by):
        """Log a patient record access to stdout.

        SEEDED ISSUE (GDPR-005): logs the full patient record including
        SSN and diagnosis on every access. Data minimization requires
        logging only the patient ID, not the full PHI payload.

        LEGACY: uses print statement (Python 2) instead of print() function.
        """
        # LEGACY: print statement — SyntaxError in Python 3.
        # Modernizer target: replace with print()
        print "[AUDIT] %s accessed by %s at %s" % (
            repr(patient),       # calls Patient.__repr__() — leaks SSN + diagnosis
            accessed_by,
            datetime.date.today().isoformat(),
        )
