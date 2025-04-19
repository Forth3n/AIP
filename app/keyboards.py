import logging
import os
import io
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "keyboards.log")

report_dir = "reports"
os.makedirs(report_dir, exist_ok=True)
html_report_path = os.path.join(report_dir, "report.html")


class HTMLHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        try:
            log_entry = self.format(record)
            with io.open(self.filename, "a", encoding="utf-8") as f:
                f.write(log_entry + "<br>\n")
        except Exception:
            self.handleError(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(file_handler)

html_handler = HTMLHandler(html_report_path)
html_handler.setFormatter(
    logging.Formatter("<b>%(asctime)s</b> [%(levelname)s] %(message)s")
)
logger.addHandler(html_handler)

logger.info("Создание главной клавиатуры")
main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Какой сегодня праздник?")],
        [KeyboardButton(text="Посмотреть личный календарь")],
    ],
    resize_keyboard=True,
)

logger.info("Создание клавиатуры выбора даты")
choose_date = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📅 Выбрать другую дату", callback_data="choose_another_date"
            )
        ]
    ]
)

logger.info("Создание клавиатуры для личного календаря")
personal_calendar_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Добавить праздник", callback_data="add_personal_holiday"
            )
        ]
    ]
)

logger.info("Все клавиатуры успешно созданы")
