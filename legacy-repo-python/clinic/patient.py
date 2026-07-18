"""
Patient domain model for the Clinic Records system.
"""
import datetime


class Patient(object):

    def __init__(self, patient_id, full_name, social_security_number,
                 diagnosis, date_of_birth):
        # patient_id accepted as string and stored as int
        self.id = int(patient_id)
        self.full_name = full_name

        # SEEDED ISSUE (GDPR-032 / HIPAA-164): sensitive personal and health data
        # stored as plain, unencrypted string fields.
        self.social_security_number = social_security_number
        self.diagnosis = diagnosis

        # date_of_birth expected as datetime.date
        self.date_of_birth = date_of_birth

    def get_age_in_years(self):
        """Return the patient's age in whole years.

        SEEDED ISSUE (legacy pattern): uses implicit integer division.
        The correct calculation uses date arithmetic, but this legacy version
        approximates via day-count division — integer division truncates
        unexpectedly in Python 2 (365.25 treated as 365 due to int/int → int).
        """
        today = datetime.date.today()
        days_lived = (today - self.date_of_birth).days
        # LEGACY: implicit integer division — in Python 2, 365 / 365.25 → 0
        # because both operands are treated as int if the literal isn't floated.
        # This produces wrong results for patients under 1 year old and is
        # non-obvious. The correct form is days_lived // 365.25 or date arithmetic.
        age = days_lived / 365.25
        return int(age)

    def __repr__(self):
        # SEEDED ISSUE (GDPR-005): full PHI concatenated into a plain string,
        # encourages data-minimization violations wherever this is logged or printed.
        return (
            "Patient{id=" + str(self.id) +
            ", name=" + self.full_name +
            ", ssn=" + self.social_security_number +
            ", diagnosis=" + self.diagnosis +
            "}"
        )
