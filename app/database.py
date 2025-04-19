import os
import sqlite3
import logging
import io

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

report_dir = "reports"
os.makedirs(report_dir, exist_ok=True)

db_folder = "database"
os.makedirs(db_folder, exist_ok=True)

log_file_path = os.path.join(log_dir, "database.log")
html_report_path = os.path.join(report_dir, "report.html")
final_html_report_path = os.path.join(report_dir, "final_report.html")
db_path = os.path.join(os.path.abspath(db_folder), "holidays.db")


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
html_handler.setFormatter(
    logging.Formatter("<b>%(asctime)s</b> [%(levelname)s] %(message)s")
)
logger.addHandler(html_handler)


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


create_db()
generate_html_report()
