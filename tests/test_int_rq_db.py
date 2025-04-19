import unittest
import sqlite3
from app.database import create_db, db_path
from app.requests import (
    add_user,
    add_personal_holiday,
    get_personal_holidays,
    delete_personal_holiday,
    delete_all_personal_holidays,
)


class TestDatabaseAndRequests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Создаём базу данных перед тестами"""
        create_db()

    def setUp(self):
        """Очищаем таблицы перед каждым тестом"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM personal_holidays")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def test_add_user(self):
        """Тестируем добавление пользователя через requests"""
        add_user(12345, "test_user")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = 12345")
        user = cursor.fetchone()

        self.assertIsNotNone(user)
        self.assertEqual(user[1], 12345)
        self.assertEqual(user[2], "test_user")

        conn.close()

    def test_add_personal_holiday(self):
        """Тестируем добавление личного праздника через requests"""
        add_user(12345, "test_user")
        add_personal_holiday(12345, "Test Holiday", "2025-12-25")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM personal_holidays WHERE user_id = 12345 AND holiday_name = 'Test Holiday'"
        )
        holiday = cursor.fetchone()

        self.assertIsNotNone(holiday)
        self.assertEqual(holiday[1], 12345)
        self.assertEqual(holiday[2], "Test Holiday")
        self.assertEqual(holiday[3], "2025-12-25")

        conn.close()

    def test_get_personal_holidays(self):
        """Тестируем получение личных праздников через requests"""
        add_user(12345, "test_user")
        add_personal_holiday(12345, "Test Holiday", "2025-12-25")
        holidays = get_personal_holidays(12345)

        self.assertEqual(len(holidays), 1)
        self.assertEqual(holidays[0][0], "Test Holiday")
        self.assertEqual(holidays[0][1], "2025-12-25")

    def test_delete_personal_holiday(self):
        """Тестируем удаление личного праздника через requests"""
        add_user(12345, "test_user")
        add_personal_holiday(12345, "Test Holiday", "2025-12-25")
        delete_personal_holiday(12345, "Test Holiday")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM personal_holidays WHERE user_id = 12345 AND holiday_name = 'Test Holiday'"
        )
        holiday = cursor.fetchone()

        self.assertIsNone(holiday)

        conn.close()

    def test_delete_all_personal_holidays(self):
        """Тестируем удаление всех личных праздников через requests"""
        add_user(12345, "test_user")
        add_personal_holiday(12345, "Test Holiday 1", "2025-12-25")
        add_personal_holiday(12345, "Test Holiday 2", "2025-12-26")
        delete_all_personal_holidays(12345)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM personal_holidays WHERE user_id = 12345")
        holidays = cursor.fetchall()

        self.assertEqual(len(holidays), 0)

        conn.close()


if __name__ == "__main__":
    unittest.main()
