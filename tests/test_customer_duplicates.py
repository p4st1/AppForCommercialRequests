import tempfile
import unittest
from pathlib import Path

from database import Database


class CustomerDuplicateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "customers.db"
        self.db = Database()
        status = self.db.open(str(self.db_path))
        self.assertEqual(status, 0)

    def tearDown(self):
        self.db.close()

    def _create_customer(
        self,
        *,
        name="Иван",
        surname="Иванов",
        patronymic="Иванович",
        email="test@example.com",
        phone="+7 (999) 123-45-67",
        company="ООО Ромашка",
    ):
        payload = (
            name,
            surname,
            patronymic,
            "",
            email,
            phone,
            company,
            "",
            "",
            "мужской",
        )
        self.db.createCustomer(payload)
        self.db.save()

    def test_detects_duplicate_by_company_and_email(self):
        self._create_customer()

        duplicate = self.db.findPotentialCustomerDuplicate(
            company_name="ООО Ромашка",
            email="test@example.com",
            phone="",
            full_name="",
        )

        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate[7], "ООО Ромашка")

    def test_detects_duplicate_by_company_and_normalized_phone(self):
        self._create_customer(phone="+7 (999) 123-45-67")

        duplicate = self.db.findPotentialCustomerDuplicate(
            company_name="ООО Ромашка",
            email="",
            phone="89991234567",
            full_name="",
        )

        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate[6], "+7 (999) 123-45-67")

    def test_exclude_customer_id_ignores_same_row(self):
        self._create_customer()
        existing = self.db.findPotentialCustomerDuplicate(
            company_name="ООО Ромашка",
            email="test@example.com",
            phone="",
            full_name="",
        )
        self.assertIsNotNone(existing)

        duplicate = self.db.findPotentialCustomerDuplicate(
            company_name="ООО Ромашка",
            email="test@example.com",
            phone="",
            full_name="",
            exclude_customer_id=int(existing[0]),
        )

        self.assertIsNone(duplicate)


if __name__ == "__main__":
    unittest.main()
