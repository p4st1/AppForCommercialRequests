from __future__ import annotations

from app.repositories.customer_repository import CustomerRepository


class CustomerService:
    def __init__(self, customer_repository: CustomerRepository):
        self._customer_repository = customer_repository

    def get_all_customers(self):
        return self._customer_repository.get_all_customers()

    def get_customers_by_company(self, company_name: str):
        return self._customer_repository.get_customers_by_company(company_name)

    def get_first_customer_by_company(self, company_name: str):
        customers = self.get_customers_by_company(company_name)
        if not customers:
            return None
        return customers[0]

    def find_potential_duplicate(
        self,
        *,
        company_name: str,
        email: str = "",
        phone: str = "",
        full_name: str = "",
        exclude_customer_id: int | None = None,
    ):
        return self._customer_repository.find_potential_duplicate(
            company_name=company_name,
            email=email,
            phone=phone,
            full_name=full_name,
            exclude_customer_id=exclude_customer_id,
        )

    def save_customer(self, data, *, edit_customer_id: int | None = None):
        if edit_customer_id is not None:
            self._customer_repository.update_customer(int(edit_customer_id), data)
        else:
            self._customer_repository.create_customer(data)
        self._customer_repository.save()

    def delete_customer_by_id(self, customer_id: int, *, commit: bool = True):
        self._customer_repository.delete_customer_by_id(int(customer_id))
        if commit:
            self._customer_repository.save()
