import os
import sqlite3
import logging
import io
import hashlib
import json
import shutil
import time
from datetime import datetime
from zipfile import ZipFile
import argparse

# Параметры
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

report_dir = "reports"
os.makedirs(report_dir, exist_ok=True)

db_folder = "database"
os.makedirs(db_folder, exist_ok=True)

archive_dir = "archive"
os.makedirs(archive_dir, exist_ok=True)

cache_file = "cache.json"
file_age_limit_days = 30  # Устаревшие файлы старше 30 дней
max_size = 100  # МБ для поиска дубликатов

log_file_path = os.path.join(log_dir, "database.log")
html_report_path = os.path.join(report_dir, "report.html")
final_html_report_path = os.path.join(report_dir, "final_report.html")
db_path = os.path.join(os.path.abspath(db_folder), "holidays.db")

# Логирование
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

# Функции работы с файлами
def file_age_in_days(file_path):
    return (time.time() - os.path.getmtime(file_path)) / (60 * 60 * 24)

def get_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def find_old_files(directory):
    old_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file_age_in_days(file_path) > file_age_limit_days:
                old_files.append(file_path)
    return old_files

def find_duplicates(directory):
    file_hashes = {}
    duplicates = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getsize(file_path) <= max_size * 1024 * 1024:
                continue  # Пропускаем файлы, которые слишком малы
            file_hash = get_file_hash(file_path)
            if file_hash in file_hashes:
                duplicates.append((file_path, file_hashes[file_hash]))
            else:
                file_hashes[file_hash] = file_path
    return duplicates

def report_disk_usage(directory):
    report = []
    for root, dirs, files in os.walk(directory):
        total_size = 0
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
        report.append(f"{root}: {total_size / (1024 * 1024):.2f} MB")
    with open("report.txt", "w", encoding="utf-8") as report_file:
        report_file.write("\n".join(report))

def archive_old_files(old_files):
    date_str = datetime.now().strftime("%Y-%m-%d")
    zip_filename = os.path.join(archive_dir, f"archive_{date_str}.zip")
    with ZipFile(zip_filename, 'w') as archive:
        for file_path in old_files:
            archive.write(file_path, os.path.basename(file_path))
            os.remove(file_path)
    logger.info(f"Архив старых файлов создан: {zip_filename}")

def cache_analysis(directory):
    cache = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            cache[file_path] = os.path.getmtime(file_path)
    with open(cache_file, "w", encoding="utf-8") as cache_file_obj:
        json.dump(cache, cache_file_obj)

def load_cache():
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as cache_file_obj:
            return json.load(cache_file_obj)
    return {}

def compare_cache_and_files(directory, cache):
    new_or_modified_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path not in cache or os.path.getmtime(file_path) > cache[file_path]:
                new_or_modified_files.append(file_path)
    return new_or_modified_files

# Создание базы данных
def create_db():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

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

        conn.commit()
        conn.close()

        logger.info(f"База данных успешно создана по пути: {db_path}")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при работе с базой данных: {e}")

# Генерация финального HTML-отчета
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

# Главная функция
def main(directory):
    logger.info(f"Начинаем анализ директории: {directory}")

    # Загружаем кэш
    cache = load_cache()

    # Ищем старые файлы
    old_files = find_old_files(directory)
    if old_files:
        logger.info(f"Найдено {len(old_files)} устаревших файлов")
        archive_old_files(old_files)
    else:
        logger.info("Устаревших файлов не найдено")

    # Ищем дубликаты
    duplicates = find_duplicates(directory)
    if duplicates:
        logger.info(f"Найдено {len(duplicates)} дубликатов")
    else:
        logger.info("Дубликатов не найдено")

    # Создаём отчет по дисковому пространству
    report_disk_usage(directory)

    # Кэшируем результаты анализа
    new_or_modified_files = compare_cache_and_files(directory, cache)
    if new_or_modified_files:
        logger.info(f"Найдено {len(new_or_modified_files)} новых или измененных файлов")
        cache_analysis(directory)
    else:
        logger.info("Нет новых или измененных файлов")

    logger.info("Анализ завершён")

# Обработка аргументов командной строки
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Анализ файловой системы.")
    parser.add_argument("directory", nargs="?", default=os.getcwd(), help="Путь к директории для анализа.")
    args = parser.parse_args()

    main(args.directory)
    create_db()
    generate_html_report()
