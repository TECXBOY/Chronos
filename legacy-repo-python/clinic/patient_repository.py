"""
Data access layer for Patient records.
"""
import hashlib
import datetime

# LEGACY: urllib2 is Python 2 only; raises ImportError in Python 3.
# Modernizer target: replace with urllib.request or requests.
import urllib2  # noqa: F401  (imported for legacy demo; not used at runtime in tests)

from clinic.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


class PatientRepository(object):

    def find_all(self):
        """Fetch all patients from the database.

        NOTE: Requires a live MySQL/PostgreSQL connection.
        Cannot be unit-tested without a real database.
        Legacy patterns present: dict.iteritems(), except E, e: syntax.
        """
        results = []

        # Simulated record store (in a real system this would be a DB cursor).
        # Using a dict with iteritems() — Python 2 pattern.
        raw_records = {
            1: {"full_name": "Alice Smith",  "ssn": "111-11-1111",
                "diagnosis": "hypertension", "dob": "1984-03-15"},
            2: {"full_name": "Bob Jones",     "ssn": "222-22-2222",
                "diagnosis": "diabetes",      "dob": "1969-07-22"},
        }

        # LEGACY: dict.iteritems() — Python 2 only; raises AttributeError in Python 3.
        # Modernizer target: replace with .items()
        for record_id, row in raw_records.iteritems():
            try:
                dob = datetime.date.fromisoformat(row["dob"])
                from clinic.patient import Patient
                p = Patient(
                    str(record_id),
                    row["full_name"],
                    row["ssn"],
                    row["diagnosis"],
                    dob,
                )
                results.append(p)
            # LEGACY: except Exception, e: syntax — SyntaxError in Python 3.
            # Modernizer target: replace with except Exception as e:
            except Exception, e:
                print "Error loading record %d: %s" % (record_id, str(e))

        return results

    def hash_for_lookup(self, value):
        """Hash a value for use as a lookup key.

        SEEDED ISSUE (SEC-002): uses bare, unsalted MD5 hash.
        SSNs occupy a small enumerable space; trivially reversible by
        precomputation. Modernizer should replace with SHA-256 at minimum;
        Compliance Officer will flag for PBKDF2 with salt.
        """
        # LEGACY: hashlib.md5 is used directly — SEC-002 violation.
        h = hashlib.md5(value.encode("utf-8"))
        return h.hexdigest()

    def _get_connection_string(self):
        return "mysql://%s:%s@%s:%d/%s" % (
            DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
        )
