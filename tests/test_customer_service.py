import unittest

from app.services.customer_service import CustomerService


class _FakeCustomerRepository:
    def __init__(self):
        self.customers = []
        self.customers_by_company = {}
        self.duplicates_result = None
        self.created_payloads = []
        self.updated_payloads = []
        self.deleted_ids = []
        self.save_calls = 0

    def get_all_customers(self):
        return list(self.customers)

    def get_customers_by_company(self, company_name: str):
        return list(self.customers_by_company.get(company_name, []))

    def find_potential_duplicate(self, **kwargs):
        self.last_duplicate_args = kwargs
        return self.duplicates_result

    def create_customer(self, data):
        self.created_payloads.append(data)

    def update_customer(self, customer_id: int, data):
        self.updated_payloads.append((customer_id, data))

    def delete_customer_by_id(self, customer_id: int):
        self.deleted_ids.append(customer_id)

    def save(self):
        self.save_calls += 1


class CustomerServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = _FakeCustomerRepository()
        self.service = CustomerService(self.repo)

    def test_get_all_customers_delegates_to_repository(self):
        self.repo.customers = [(1, "A"), (2, "B")]

        result = self.service.get_all_customers()

        self.assertEqual(result, [(1, "A"), (2, "B")])

    def test_get_first_customer_by_company_returns_first_or_none(self):
        self.repo.customers_by_company = {
            "ООО Ромашка": [(10, "", "", "", "", "", "", "ООО Ромашка")]
        }

        first = self.service.get_first_customer_by_company("ООО Ромашка")
        missing = self.service.get_first_customer_by_company("ООО Нет")

        self.assertEqual(first[0], 10)
        self.assertIsNone(missing)

    def test_find_potential_duplicate_forwards_arguments(self):
        self.repo.duplicates_result = ("duplicate",)

        result = self.service.find_potential_duplicate(
            company_name="ООО Ромашка",
            email="test@example.com",
            phone="+79991234567",
            full_name="Иванов Иван Иванович",
            exclude_customer_id=5,
        )

        self.assertEqual(result, ("duplicate",))
        self.assertEqual(self.repo.last_duplicate_args["company_name"], "ООО Ромашка")
        self.assertEqual(self.repo.last_duplicate_args["exclude_customer_id"], 5)

    def test_save_customer_creates_new_customer_when_edit_id_absent(self):
        payload = ("name", "surname")

        self.service.save_customer(payload, edit_customer_id=None)

        self.assertEqual(self.repo.created_payloads, [payload])
        self.assertEqual(self.repo.updated_payloads, [])
        self.assertEqual(self.repo.save_calls, 1)

    def test_save_customer_updates_existing_customer_when_edit_id_provided(self):
        payload = ("name", "surname")

        self.service.save_customer(payload, edit_customer_id=42)

        self.assertEqual(self.repo.created_payloads, [])
        self.assertEqual(self.repo.updated_payloads, [(42, payload)])
        self.assertEqual(self.repo.save_calls, 1)

    def test_delete_customer_by_id_can_skip_commit(self):
        self.service.delete_customer_by_id(7, commit=False)

        self.assertEqual(self.repo.deleted_ids, [7])
        self.assertEqual(self.repo.save_calls, 0)

    def test_delete_customer_by_id_commits_by_default(self):
        self.service.delete_customer_by_id(7)

        self.assertEqual(self.repo.deleted_ids, [7])
        self.assertEqual(self.repo.save_calls, 1)


if __name__ == "__main__":
    unittest.main()
