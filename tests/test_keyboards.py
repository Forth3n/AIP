import unittest
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


class TestKeyboards(unittest.TestCase):

    def test_main_keyboard(self):
        main = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Какой сегодня праздник?")],
                [KeyboardButton(text="Посмотреть личный календарь")],
            ],
            resize_keyboard=True,
        )
        self.assertEqual(len(main.keyboard), 2)
        self.assertEqual(main.keyboard[0][0].text, "Какой сегодня праздник?")
        self.assertEqual(main.keyboard[1][0].text, "Посмотреть личный календарь")

    def test_choose_date_keyboard(self):
        choose_date = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📅 Выбрать другую дату",
                        callback_data="choose_another_date",
                    )
                ]
            ]
        )
        self.assertEqual(len(choose_date.inline_keyboard), 1)
        self.assertEqual(
            choose_date.inline_keyboard[0][0].text, "📅 Выбрать другую дату"
        )

    def test_personal_calendar_keyboard(self):
        personal_calendar_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Добавить праздник",
                        callback_data="add_personal_holiday",
                    )
                ]
            ]
        )
        self.assertEqual(len(personal_calendar_kb.inline_keyboard), 1)
        self.assertEqual(
            personal_calendar_kb.inline_keyboard[0][0].text, "➕ Добавить праздник"
        )


if __name__ == "__main__":
    unittest.main()
