"""
Outbound notification service for the Clinic Records system.
"""
# LEGACY: urllib2 is Python 2 only.
# Modernizer target: replace with urllib.request (stdlib) or requests (third-party).
import urllib2  # noqa: F401

from clinic.config import NOTIFICATION_API_KEY


class NotificationService(object):

    def send_reminder(self, patient):
        """Send an appointment reminder to a patient.

        SEEDED ISSUE (SEC-001): the live API key is printed to stdout on
        every call. Even after the hardcoded literal is removed from config.py,
        any logging infrastructure capturing stdout will record the secret.

        LEGACY: uses print statement (Python 2).
        """
        # SEEDED ISSUE (SEC-001): prints the API key on every call.
        # LEGACY: print statement — SyntaxError in Python 3.
        print "Sending reminder to %s using key %s" % (
            patient.full_name,
            NOTIFICATION_API_KEY,
        )
