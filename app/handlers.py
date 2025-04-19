import os
import logging
import io
import datetime
import requests
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from deep_translator import GoogleTranslator
import app.database as db
import app.keyboards as kb
import app.requests as rq
import zipfile
import time
import json

# Настройка логирования
log_dir = "logs"
report_dir = "reports"
os.makedirs(log_dir, exist_ok=True)
os.makedirs(report_dir, exist_ok=True)

log_file_path = os.path.join(log_dir, "handlers.log")
html_report_path = os.path.join(report_dir, "report.html")
final_html_report_path = os.path.join(report_dir, "final_report.html")
cache_file_path = "cache.json"

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

log_handler = logging.FileHandler(log_file_path, encoding="utf-8")
log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(log_handler)

html_handler = HTMLHandler(html_report_path)
html_handler.setFormatter(logging.Formatter("<b>%(asctime)s</b> [%(levelname)s] %(message)s"))
logger.addHandler(html_handler)

# Функция для анализа файлов и нахождения устаревших файлов
def analyze_directory(directory):
    current_time = time.time()
    outdated_files = []
    file_sizes = {}
    duplicates = []

    # Пройдем по всем файлам в директории
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_stat = os.stat(file_path)
            file_age = current_time - file_stat.st_mtime

            # Находим устаревшие файлы
            if file_age > 30 * 24 * 60 * 60:  # более 30 дней
                outdated_files.append(file_path)
                logger.info(f"Устаревший файл: {file_path} (возраст: {file_age / (24 * 60 * 60):.2f} дней)")

            # Находим дубликаты
            file_size = file_stat.st_size
            if file_size in file_sizes:
                file_sizes[file_size].append(file_path)
                if len(file_sizes[file_size]) == 2:
                    duplicates.append(file_sizes[file_size])
                    logger.info(f"Найден дубликат: {file_sizes[file_size][0]} и {file_sizes[file_size][1]}")
            else:
                file_sizes[file_size] = [file_path]

    return outdated_files, duplicates

# Функция для архивации устаревших файлов в ZIP
def archive_outdated_files(outdated_files):
    archive_name = f"outdated_files_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
    with zipfile.ZipFile(archive_name, "w") as archive:
        for file in outdated_files:
            archive.write(file, os.path.basename(file))
            logger.info(f"Добавлен в архив: {file}")
    logger.info(f"Архив устаревших файлов создан: {archive_name}")

# Функция для создания кэша с результатами анализа
def create_cache(directory, outdated_files, duplicates):
    cache_data = {
        "directory": directory,
        "outdated_files": outdated_files,
        "duplicates": duplicates,
        "timestamp": datetime.datetime.now().isoformat()
    }
    with open(cache_file_path, "w", encoding="utf-8") as cache_file:
        json.dump(cache_data, cache_file, indent=4)
    logger.info(f"Кэш создан и сохранён в {cache_file_path}")

# Генерация HTML-отчёта
def generate_html_report():
    try:
        with io.open(html_report_path, "r", encoding="utf-8") as log_file:
            log_entries = log_file.readlines()

        html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Итоговый отчёт логов</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            padding: 20px;
        }}
        h1 {{
            color: #333;
        }}
        .log {{
            background-color: #fff;
            border: 1px solid #ccc;
            padding: 10px;
            line-height: 1.6;
        }}
        .INFO {{ color: green; }}
        .ERROR {{ color: red; }}
        .WARNING {{ color: orange; }}
        .DEBUG {{ color: gray; }}
    </style>
</head>
<body>
    <h1>Итоговый отчёт логов</h1>
    <div class="log">
        {''.join(log_entries)}
    </div>
</body>
</html>"""

        with io.open(final_html_report_path, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)

        logger.info(f"HTML-отчёт успешно сохранён: {final_html_report_path}")
    except Exception as e:
        logger.error(f"Ошибка при создании итогового HTML-отчёта: {e}")

# Основная функция
def main(directory):
    logger.info(f"Запуск анализа директории: {directory}")
    outdated_files, duplicates = analyze_directory(directory)
    create_cache(directory, outdated_files, duplicates)

    if outdated_files:
        logger.info("Архивация устаревших файлов...")
        archive_outdated_files(outdated_files)
    else:
        logger.info("Устаревшие файлы не найдены.")

# Вызов основной функции с текущей директорией
main(os.getcwd())
router = Router()
API = "ijx15Q1EWw2iAn8lBuH6S2wdZRH5yLXE"


class HolidayDate(StatesGroup):
    waiting_for_date = State()
    waiting_for_custom_date = State()
    waiting_for_custom_name = State()


db.create_db()


def get_holidays_by_date(date: datetime.date, country_code="KZ"):
    url = "https://calendarific.com/api/v2/holidays"
    params = {
        "api_key": API,
        "country": country_code,
        "year": date.year,
        "month": date.month,
        "day": date.day,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("response", {}).get("holidays", [])
    except (requests.RequestException, ValueError) as e:
        logger.error(f"Ошибка получения праздников: {e}")
        return None


def translate_to_russian(text: str) -> str:
    try:
        return GoogleTranslator(source="auto", target="ru").translate(text)
    except Exception as e:
        logger.warning(f"Ошибка перевода: {e}")
        return text


def create_delete_holiday_keyboard(holidays):
    buttons = []

    for holiday in holidays:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ {holiday[0]}",
                    callback_data=f"delete_holiday_{holiday[0]}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="➕ Добавить праздник", callback_data="add_personal_holiday"
            ),
            InlineKeyboardButton(
                text="🗑 Удалить все", callback_data="delete_all_holidays"
            ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: Message):
    rq.add_user(message.from_user.id, message.from_user.username)
    logger.info(
        f"Команда /start от пользователя {message.from_user.id} ({message.from_user.username})"
    )
    await message.answer("Привет! Выбери пункт на клавиатуре", reply_markup=kb.main)


@router.message(F.text == "Какой сегодня праздник?")
async def cmd_today(message: Message):
    today = datetime.date.today()
    logger.info(f"Запрос на праздник на сегодня от {message.from_user.id} — {today}")
    holidays = get_holidays_by_date(today)
    if holidays is None:
        text = "Не удалось получить данные. Попробуйте позже."
    elif holidays:
        text = f"Сегодня ({today.strftime('%d.%m.%Y')}) отмечаются:\n\n"
        for h in holidays:
            text += f"🎉 {translate_to_russian(h['name'])}\n"
    else:
        text = f"Сегодня ({today.strftime('%d.%m.%Y')}) нет официальных праздников"
    await message.answer(text, reply_markup=kb.choose_date)


@router.callback_query(F.data == "choose_another_date")
async def cb_pick_another_date(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Пользователь {callback.from_user.id} выбрал ввод другой даты")
    await callback.message.answer("Введите дату в формате **дд.мм.гггг**:")
    await state.set_state(HolidayDate.waiting_for_date)
    await callback.answer()


@router.message(HolidayDate.waiting_for_date)
async def process_custom_date(message: Message, state: FSMContext):
    try:
        date = datetime.datetime.strptime(message.text, "%d.%m.%Y").date()
        logger.info(f"Пользователь {message.from_user.id} ввёл дату: {date}")
    except ValueError:
        logger.warning(
            f"Пользователь {message.from_user.id} ввёл неверную дату: {message.text}"
        )
        await message.reply("❌ Неверный формат даты. Попробуйте ещё раз: дд.мм.гггг")
        return
    holidays = get_holidays_by_date(date)
    if holidays is None:
        text = "Не удалось получить данные. Попробуйте позже."
    elif holidays:
        text = f"На {date.strftime('%d.%m.%Y')} отмечаются:\n\n"
        for h in holidays:
            text += f"🎉 {translate_to_russian(h['name'])}\n"
    else:
        text = f"На {date.strftime('%d.%m.%Y')} нет официальных праздников."
    await message.answer(text, reply_markup=kb.choose_date)
    await state.clear()


@router.message(F.text == "Посмотреть личный календарь")
async def cmd_personal_calendar(message: Message):
    logger.info(f"Пользователь {message.from_user.id} запросил личный календарь")
    holidays = rq.get_personal_holidays(message.from_user.id)
    if holidays:
        text = "Ваши личные праздники:\n\n"
        for holiday in holidays:
            text += f"🎉 {holiday[0]} — {holiday[1]}\n"
        keyboard = create_delete_holiday_keyboard(holidays)
    else:
        text = "Ваш календарь пуст. Вы можете добавить личные праздники."
        keyboard = kb.personal_calendar_kb
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "add_personal_holiday")
async def add_personal_holiday(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Пользователь {callback.from_user.id} начал добавление праздника")
    await callback.message.answer("Введите дату праздника в формате дд.мм.гггг:")
    await state.set_state(HolidayDate.waiting_for_custom_date)
    await callback.answer()


@router.message(HolidayDate.waiting_for_custom_date)
async def handle_personal_date(message: Message, state: FSMContext):
    try:
        date = datetime.datetime.strptime(message.text, "%d.%m.%Y").date()
        logger.info(
            f"Пользователь {message.from_user.id} указал дату личного праздника: {date}"
        )
    except ValueError:
        logger.warning(
            f"Пользователь {message.from_user.id} указал неверную дату: {message.text}"
        )
        await message.reply("❌ Неверный формат даты. Попробуйте снова: дд.мм.гггг")
        return
    await state.update_data(holiday_date=date)
    await state.set_state(HolidayDate.waiting_for_custom_name)
    await message.answer("Введите название праздника:")


@router.message(HolidayDate.waiting_for_custom_name)
async def handle_personal_name(message: Message, state: FSMContext):
    holiday_name = message.text
    user_data = await state.get_data()
    holiday_date = user_data["holiday_date"]
    rq.add_personal_holiday(message.from_user.id, holiday_name, holiday_date)
    logger.info(
        f"Пользователь {message.from_user.id} добавил праздник '{holiday_name}' ({holiday_date})"
    )
    await message.answer(
        f"🎉 Праздник '{holiday_name}' на {holiday_date.strftime('%d.%m.%Y')} успешно добавлен!"
    )
    await state.clear()


@router.callback_query(F.data.startswith("delete_holiday_"))
async def delete_personal_holiday(callback: CallbackQuery):
    holiday_name = callback.data.split("_", 2)[2]
    rq.delete_personal_holiday(callback.from_user.id, holiday_name)
    logger.info(
        f"Пользователь {callback.from_user.id} удалил личный праздник '{holiday_name}'"
    )

    holidays = rq.get_personal_holidays(callback.from_user.id)
    if holidays:
        text = "Праздник удалён. Ваши оставшиеся личные праздники:\n\n"
        for holiday in holidays:
            text += f"🎉 {holiday[0]} — {holiday[1]}\n"
        keyboard = create_delete_holiday_keyboard(holidays)
    else:
        text = "Календарь пуст. Вы можете добавить личные праздники."
        keyboard = kb.personal_calendar_kb

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "delete_all_holidays")
async def confirm_delete_all_personal_holidays(callback: CallbackQuery):
    rq.delete_all_personal_holidays(callback.from_user.id)
    logger.info(f"Пользователь {callback.from_user.id} удалил все личные праздники")
    await callback.message.answer("Ваш календарь очищен.")
    await cmd_personal_calendar(callback.message)


generate_html_report()
