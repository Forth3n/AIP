import sys
import os
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import datetime
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.handlers import (
    get_holidays_by_date,
    translate_to_russian,
    handle_personal_date,
    HolidayDate,
)


class TestHandlers(unittest.IsolatedAsyncioTestCase):
    @patch("app.handlers.requests.get")
    def test_get_holidays_by_date_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "response": {"holidays": [{"name": "Some Holiday"}]}
        }

        date = datetime.date(2024, 1, 1)
        holidays = get_holidays_by_date(date)
        self.assertEqual(len(holidays), 1)
        self.assertEqual(holidays[0]["name"], "Some Holiday")

    @patch("app.handlers.requests.get")
    def test_get_holidays_by_date_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("API error")
        date = datetime.date(2024, 1, 1)
        holidays = get_holidays_by_date(date)
        self.assertIsNone(holidays)

    def test_translate_to_russian(self):
        result = translate_to_russian("Hello")
        self.assertIsInstance(result, str)

    @patch("app.handlers.rq.add_personal_holiday")
    async def test_handle_personal_date_valid(self, mock_add):
        message = MagicMock()
        message.text = "01.01.2025"
        message.answer = AsyncMock()
        state = AsyncMock()
        await handle_personal_date(message, state)
        state.update_data.assert_called()
        state.set_state.assert_called_with(HolidayDate.waiting_for_custom_name)

    async def test_handle_personal_date_invalid(self):
        message = MagicMock()
        message.text = "не дата"
        message.reply = AsyncMock()
        state = AsyncMock()
        await handle_personal_date(message, state)
        message.reply.assert_awaited_with(
            "❌ Неверный формат даты. Попробуйте снова: дд.мм.гггг"
        )


if __name__ == "__main__":
    unittest.main()
