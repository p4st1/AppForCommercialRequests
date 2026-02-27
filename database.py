from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sqlite3


class Database:
    def __init__(self):
        self.connection: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None

    def _require_cursor(self) -> sqlite3.Cursor:
        if self.cursor is None:
            raise RuntimeError("База данных не открыта")
        return self.cursor

    def create(self):
        cursor = self._require_cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS offers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_number INTEGER NOT NULL,
                date TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '',
                surname TEXT NOT NULL DEFAULT '',
                patronymic TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                phoneNumber TEXT NOT NULL DEFAULT '',
                companyName TEXT NOT NULL DEFAULT '',
                post TEXT NOT NULL DEFAULT '',
                conditions TEXT NOT NULL DEFAULT '',
                sex TEXT NOT NULL DEFAULT 'мужской'
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_customers_company
            ON customers(companyName)
            """
        )

    def _get_columns(self, table_name: str) -> list[str]:
        cursor = self._require_cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]

    def _migrate_offers(self):
        cursor = self._require_cursor()
        columns = self._get_columns("offers")
        if {"id", "offer_number", "date"}.issubset(columns):
            return

        cursor.execute("ALTER TABLE offers RENAME TO offers_legacy")
        cursor.execute(
            """
            CREATE TABLE offers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_number INTEGER NOT NULL,
                date TEXT NOT NULL
            )
            """
        )

        cursor.execute("PRAGMA table_info(offers_legacy)")
        legacy_columns = {row[1] for row in cursor.fetchall()}
        if {"id", "date"}.issubset(legacy_columns):
            cursor.execute("SELECT id, date FROM offers_legacy ORDER BY id")
            rows = cursor.fetchall()
            counters: dict[str, int] = {}
            for old_id, raw_date in rows:
                text_date = str(raw_date or "").strip()
                try:
                    datetime.strptime(text_date, "%Y-%m-%d")
                except ValueError:
                    continue

                counters[text_date] = counters.get(text_date, 0) + 1
                offer_number = counters[text_date]

                # Если в старой схеме id был валидным положительным числом, используем его
                # как исходный номер предложения в этот день.
                try:
                    parsed_id = int(old_id)
                    if parsed_id > 0:
                        offer_number = max(offer_number, parsed_id)
                        counters[text_date] = offer_number
                except (TypeError, ValueError):
                    pass

                cursor.execute(
                    "INSERT INTO offers (offer_number, date) VALUES (?, ?)",
                    (offer_number, text_date),
                )

        cursor.execute("DROP TABLE offers_legacy")

    def open(self, filename: str):
        try:
            self.connection = sqlite3.connect(filename)
            self.cursor = self.connection.cursor()
            self.create()
            self._migrate_offers()
            self.save()
            return 0
        except Exception:
            self.connection = None
            self.cursor = None
            return -1

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            self.cursor = None

    def save(self):
        if self.connection is not None:
            self.connection.commit()

    @staticmethod
    def _normalize_customer_payload(data):
        values = list(data[:10]) + [""] * (10 - len(data))
        normalized = [str(value or "").strip() for value in values[:10]]
        if normalized[9] not in {"мужской", "женский"}:
            normalized[9] = "мужской"
        return tuple(normalized)

    def createOffer(self):
        cursor = self._require_cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COALESCE(MAX(offer_number), 0) + 1 FROM offers WHERE date = ?",
            (today,),
        )
        next_offer = int(cursor.fetchone()[0])
        cursor.execute(
            "INSERT INTO offers (offer_number, date) VALUES (?, ?)",
            (next_offer, today),
        )
        return next_offer

    def createCustomer(self, data):
        payload = self._normalize_customer_payload(data)
        cursor = self._require_cursor()
        cursor.execute(
            """
            INSERT INTO customers (
                name,
                surname,
                patronymic,
                address,
                email,
                phoneNumber,
                companyName,
                post,
                conditions,
                sex
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )

    def updateCustomer(self, customer_id: int, data):
        payload = self._normalize_customer_payload(data)
        cursor = self._require_cursor()
        cursor.execute(
            """
            UPDATE customers SET
                name = ?,
                surname = ?,
                patronymic = ?,
                address = ?,
                email = ?,
                phoneNumber = ?,
                companyName = ?,
                post = ?,
                conditions = ?,
                sex = ?
            WHERE id = ?
            """,
            (*payload, int(customer_id)),
        )

    def getAllCustomers(self):
        cursor = self._require_cursor()
        cursor.execute("SELECT * FROM customers ORDER BY companyName COLLATE NOCASE")
        return cursor.fetchall()

    def getCustomer(self, name):
        cursor = self._require_cursor()
        cursor.execute(
            "SELECT * FROM customers WHERE companyName = ? ORDER BY id",
            (name,),
        )
        return cursor.fetchall()

    def delCustomer(self, name):
        cursor = self._require_cursor()
        cursor.execute("DELETE FROM customers WHERE companyName = ?", (name,))

    def delCustomerById(self, customer_id: int):
        cursor = self._require_cursor()
        cursor.execute("DELETE FROM customers WHERE id = ?", (int(customer_id),))

    def upsertCustomer(self, data):
        payload = self._normalize_customer_payload(data)
        cursor = self._require_cursor()
        cursor.execute(
            """
            SELECT id
            FROM customers
            WHERE companyName = ? AND name = ? AND surname = ? AND patronymic = ?
            ORDER BY id
            LIMIT 1
            """,
            (payload[6], payload[0], payload[1], payload[2]),
        )
        row = cursor.fetchone()
        if row:
            self.updateCustomer(row[0], payload)
            return row[0], False

        self.createCustomer(payload)
        return cursor.lastrowid, True

    def export(self, source, target):
        if not source or not target:
            return -1
        shutil.copy2(source, target)
        return 0

    def import_(self, source, target):
        if not source or not target:
            return -1
        source_path = Path(source)
        if not source_path.exists():
            return -1

        source_conn = None
        target_db = None
        try:
            source_conn = sqlite3.connect(str(source_path))
            source_cursor = source_conn.cursor()
            source_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='customers'"
            )
            if source_cursor.fetchone() is None:
                return -1

            source_cursor.execute(
                """
                SELECT
                    name, surname, patronymic, address, email, phoneNumber,
                    companyName, post, conditions, sex
                FROM customers
                """
            )
            customers = source_cursor.fetchall()

            target_db = Database()
            if target_db.open(target) == -1:
                return -1

            for customer in customers:
                target_db.upsertCustomer(customer)
            target_db.save()
            return 0
        except Exception:
            return -1
        finally:
            if source_conn is not None:
                source_conn.close()
            if target_db is not None:
                target_db.close()
