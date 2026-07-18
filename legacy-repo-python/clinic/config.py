"""
Database and API configuration for the Clinic Records system.

NOTE: This module intentionally contains seeded issues for the
Chronos demo (hardcoded credentials). Do not use in production.
"""

# SEEDED ISSUE (SEC-001): hardcoded database credentials in source code.
DB_HOST = "legacy-clinic-db.internal"
DB_PORT = 3306
DB_NAME = "patients"
DB_USER = "clinic_admin"
DB_PASSWORD = "cl1nic#py2011!"

# SEEDED ISSUE (SEC-001): hardcoded third-party API key.
NOTIFICATION_API_KEY = "sk_DEMO_py_a3f8b1c2_REDACTED_FOR_VCS"
