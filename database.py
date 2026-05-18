from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sqlite3
import re
from tools import DatabaseTools as Tool


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
        self._create_offers_table()
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

    def _create_offers_table(self):
        cursor = self._require_cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS offers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_number INTEGER NOT NULL DEFAULT 0,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT '',
                event_type TEXT NOT NULL DEFAULT 'docx',
                customer_company TEXT NOT NULL DEFAULT '',
                customer_name TEXT NOT NULL DEFAULT '',
                items_count INTEGER NOT NULL DEFAULT 0,
                total_amount REAL,
                currency TEXT NOT NULL DEFAULT '',
                file_path TEXT NOT NULL DEFAULT '',
                remote_url TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                payload_json TEXT NOT NULL DEFAULT ''
            )
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
        self._create_offers_table()

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
                old_id_text = str(old_id or "").strip()
                if old_id_text.isdigit():
                    parsed_id = int(old_id_text)
                    if parsed_id > 0:
                        offer_number = max(offer_number, parsed_id)
                        counters[text_date] = offer_number

                cursor.execute(
                    """
                    INSERT INTO offers (
                        offer_number,
                        date,
                        created_at,
                        event_type
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (offer_number, text_date, f"{text_date} 00:00:00", "docx"),
                )

        cursor.execute("DROP TABLE offers_legacy")

    def _ensure_offers_columns(self):
        cursor = self._require_cursor()
        columns = set(self._get_columns("offers"))
        required_columns = {
            "created_at": "TEXT NOT NULL DEFAULT ''",
            "event_type": "TEXT NOT NULL DEFAULT 'docx'",
            "customer_company": "TEXT NOT NULL DEFAULT ''",
            "customer_name": "TEXT NOT NULL DEFAULT ''",
            "items_count": "INTEGER NOT NULL DEFAULT 0",
            "total_amount": "REAL",
            "currency": "TEXT NOT NULL DEFAULT ''",
            "file_path": "TEXT NOT NULL DEFAULT ''",
            "remote_url": "TEXT NOT NULL DEFAULT ''",
            "notes": "TEXT NOT NULL DEFAULT ''",
            "payload_json": "TEXT NOT NULL DEFAULT ''",
        }

        for name, definition in required_columns.items():
            if name in columns:
                continue
            cursor.execute(f"ALTER TABLE offers ADD COLUMN {name} {definition}")

        cursor.execute(
            """
            UPDATE offers
            SET created_at = CASE
                WHEN LENGTH(date) = 10 THEN date || ' 00:00:00'
                ELSE COALESCE(created_at, '')
            END
            WHERE COALESCE(created_at, '') = ''
            """
        )
        cursor.execute(
            """
            UPDATE offers
            SET event_type = 'docx'
            WHERE COALESCE(event_type, '') = ''
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_offers_created_at
            ON offers(created_at)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_offers_date
            ON offers(date)
            """
        )

    def open(self, filename: str):
        try:
            self.connection = sqlite3.connect(filename)
            self.cursor = self.connection.cursor()
            self.create()
            self._migrate_offers()
            self._ensure_offers_columns()
            self.save()
            return 0
        except Exception as e:
            Tool.log_exception(
                f"Не удалось открыть БД: {filename}",
                e,
                include_traceback=True,
            )
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

    def _next_offer_number(self, date_value: str) -> int:
        cursor = self._require_cursor()
        cursor.execute(
            """
            SELECT COALESCE(MAX(offer_number), 0) + 1
            FROM offers
            WHERE date = ? AND event_type = 'docx'
            """,
            (date_value,),
        )
        return int(cursor.fetchone()[0])

    def getNextOfferNumber(self, date_value: str | None = None) -> int:
        date_to_use = date_value or datetime.now().strftime("%Y-%m-%d")
        return self._next_offer_number(date_to_use)

    def addHistoryEvent(
        self,
        event_type: str,
        customer_company: str = "",
        customer_name: str = "",
        items_count: int = 0,
        total_amount: float | None = None,
        currency: str = "",
        file_path: str = "",
        remote_url: str = "",
        notes: str = "",
        payload_json: str = "",
    ) -> int:
        cursor = self._require_cursor()
        now = datetime.now()
        date_value = now.strftime("%Y-%m-%d")
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")
        normalized_type = str(event_type or "").strip().lower() or "other"
        offer_number = self._next_offer_number(date_value) if normalized_type == "docx" else 0
        items_value = max(0, int(items_count or 0))
        total_value = None if total_amount is None else float(total_amount)

        cursor.execute(
            """
            INSERT INTO offers (
                offer_number,
                date,
                created_at,
                event_type,
                customer_company,
                customer_name,
                items_count,
                total_amount,
                currency,
                file_path,
                remote_url,
                notes,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                offer_number,
                date_value,
                created_at,
                normalized_type,
                str(customer_company or "").strip(),
                str(customer_name or "").strip(),
                items_value,
                total_value,
                str(currency or "").strip(),
                str(file_path or "").strip(),
                str(remote_url or "").strip(),
                str(notes or "").strip(),
                str(payload_json or ""),
            ),
        )
        return offer_number

    def createOffer(
        self,
        customer_company: str = "",
        customer_name: str = "",
        items_count: int = 0,
        total_amount: float | None = None,
        currency: str = "",
        file_path: str = "",
        remote_url: str = "",
        notes: str = "",
        payload_json: str = "",
    ) -> int:
        return self.addHistoryEvent(
            event_type="docx",
            customer_company=customer_company,
            customer_name=customer_name,
            items_count=items_count,
            total_amount=total_amount,
            currency=currency,
            file_path=file_path,
            remote_url=remote_url,
            notes=notes,
            payload_json=payload_json,
        )

    def getOffersHistory(self, limit: int = 500):
        cursor = self._require_cursor()
        safe_limit = max(1, int(limit))
        cursor.execute(
            """
            SELECT
                id,
                offer_number,
                date,
                created_at,
                event_type,
                customer_company,
                customer_name,
                items_count,
                total_amount,
                currency,
                file_path,
                remote_url,
                notes,
                payload_json
            FROM offers
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (safe_limit,),
        )
        return cursor.fetchall()

    def deleteHistoryEvent(self, event_id: int):
        cursor = self._require_cursor()
        cursor.execute("DELETE FROM offers WHERE id = ?", (int(event_id),))

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

    @staticmethod
    def _normalize_text(value: str) -> str:
        return str(value or "").strip().casefold()

    @staticmethod
    def _normalize_phone(value: str) -> str:
        digits = re.sub(r"\D+", "", str(value or ""))
        if len(digits) > 10:
            return digits[-10:]
        return digits

    def findPotentialCustomerDuplicate(
        self,
        *,
        company_name: str,
        email: str = "",
        phone: str = "",
        full_name: str = "",
        exclude_customer_id: int | None = None,
    ):
        company_norm = self._normalize_text(company_name)
        if not company_norm:
            return None

        email_norm = self._normalize_text(email)
        phone_norm = self._normalize_phone(phone)
        full_name_norm = self._normalize_text(full_name)

        for customer in self.getAllCustomers():
            customer_id = int(customer[0])
            if exclude_customer_id is not None and customer_id == int(exclude_customer_id):
                continue

            existing_company_norm = self._normalize_text(customer[7])
            if existing_company_norm != company_norm:
                continue

            existing_email_norm = self._normalize_text(customer[5])
            existing_phone_norm = self._normalize_phone(customer[6])
            existing_full_name_norm = self._normalize_text(
                " ".join(part for part in [customer[2], customer[1], customer[3]] if str(part).strip())
            )

            same_email = bool(email_norm and existing_email_norm == email_norm)
            same_phone = bool(phone_norm and existing_phone_norm == phone_norm)
            same_full_name = bool(full_name_norm and existing_full_name_norm == full_name_norm)
            no_identifiers = not email_norm and not phone_norm and not full_name_norm

            if same_email or same_phone or same_full_name or no_identifiers:
                return customer
        return None

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
        except Exception as e:
            Tool.log_exception(
                f"Ошибка импорта БД из {source} в {target}",
                e,
                include_traceback=True,
            )
            return -1
        finally:
            if source_conn is not None:
                source_conn.close()
            if target_db is not None:
                target_db.close()
