from __future__ import annotations

from database import Database


class CustomerRepository:
    def __init__(self, db: Database):
        self._db = db

    def get_all_customers(self):
        return self._db.getAllCustomers()

    def get_customers_by_company(self, company_name: str):
        return self._db.getCustomer(company_name)

    def find_potential_duplicate(
        self,
        *,
        company_name: str,
        email: str = "",
        phone: str = "",
        full_name: str = "",
        exclude_customer_id: int | None = None,
    ):
        return self._db.findPotentialCustomerDuplicate(
            company_name=company_name,
            email=email,
            phone=phone,
            full_name=full_name,
            exclude_customer_id=exclude_customer_id,
        )

    def create_customer(self, data):
        self._db.createCustomer(data)

    def update_customer(self, customer_id: int, data):
        self._db.updateCustomer(customer_id, data)

    def delete_customer_by_id(self, customer_id: int):
        self._db.delCustomerById(customer_id)

    def save(self):
        self._db.save()
