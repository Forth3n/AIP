import unittest
import sqlite3
from app.requests import (
    add_user,
    add_personal_holiday,
    get_personal_holidays,
    delete_personal_holiday,
    delete_all_personal_holidays,
)
from app.database import db_path


class TestDatabaseFunctions(unittest.TestCase):
    def setUp(self):
        self.test_user_id = 9999
        self.test_username = "test_user"
        self.test_holiday_name = "Test Day"
        self.test_holiday_date = "2025-12-31"

        # Создание таблиц, если их нет
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS personal_holidays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    holiday_name TEXT,
                    holiday_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """
            )
            conn.commit()

    def tearDown(self):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM personal_holidays WHERE user_id = ?", (self.test_user_id,)
            )
            cursor.execute("DELETE FROM users WHERE user_id = ?", (self.test_user_id,))
            conn.commit()

    def test_add_user(self):
        add_user(self.test_user_id, self.test_username)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username FROM users WHERE user_id = ?", (self.test_user_id,)
            )
            result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], self.test_username)

    def test_add_and_get_personal_holiday(self):
        add_user(self.test_user_id, self.test_username)
        add_personal_holiday(
            self.test_user_id, self.test_holiday_name, self.test_holiday_date
        )
        holidays = get_personal_holidays(self.test_user_id)
        self.assertEqual(len(holidays), 1)
        self.assertEqual(holidays[0], (self.test_holiday_name, self.test_holiday_date))

    def test_delete_personal_holiday(self):
        add_user(self.test_user_id, self.test_username)
        add_personal_holiday(
            self.test_user_id, self.test_holiday_name, self.test_holiday_date
        )
        delete_personal_holiday(self.test_user_id, self.test_holiday_name)
        holidays = get_personal_holidays(self.test_user_id)
        self.assertEqual(len(holidays), 0)

    def test_delete_all_personal_holidays(self):
        add_user(self.test_user_id, self.test_username)
        add_personal_holiday(self.test_user_id, "Test 1", "2025-12-01")
        add_personal_holiday(self.test_user_id, "Test 2", "2025-12-02")
        delete_all_personal_holidays(self.test_user_id)
        holidays = get_personal_holidays(self.test_user_id)
        self.assertEqual(len(holidays), 0)


if __name__ == "__main__":
    unittest.main()
