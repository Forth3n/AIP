import unittest
import sqlite3
from app import requests


class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        self.memory_db = sqlite3.connect(":memory:")
        self.memory_db.row_factory = sqlite3.Row
        cursor = self.memory_db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                username TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS personal_holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                holiday_name TEXT NOT NULL,
                holiday_date DATE NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """
        )
        self.memory_db.commit()
        self.original_connect = sqlite3.connect
        sqlite3.connect = lambda _: self.memory_db

    def tearDown(self):
        sqlite3.connect = self.original_connect
        self.memory_db.close()

    def test_add_user(self):
        requests.add_user(1, "Alice")
        cursor = self.memory_db.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = 1")
        user = cursor.fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user["user_id"], 1)
        self.assertEqual(user["username"], "Alice")

    def test_add_and_get_personal_holiday(self):
        requests.add_user(2, "Bob")
        requests.add_personal_holiday(2, "Birthday", "2025-06-01")
        holidays = requests.get_personal_holidays(2)
        self.assertEqual(len(holidays), 1)
        self.assertEqual(holidays[0]["holiday_name"], "Birthday")
        self.assertEqual(holidays[0]["holiday_date"], "2025-06-01")

    def test_delete_personal_holiday(self):
        requests.add_user(3, "Charlie")
        requests.add_personal_holiday(3, "Test Day", "2025-01-01")
        requests.delete_personal_holiday(3, "Test Day")
        holidays = requests.get_personal_holidays(3)
        self.assertEqual(len(holidays), 0)

    def test_delete_all_personal_holidays(self):
        requests.add_user(4, "Dave")
        requests.add_personal_holiday(4, "Event1", "2025-01-01")
        requests.add_personal_holiday(4, "Event2", "2025-02-02")
        requests.delete_all_personal_holidays(4)
        holidays = requests.get_personal_holidays(4)
        self.assertEqual(len(holidays), 0)


if __name__ == "__main__":
    unittest.main()
