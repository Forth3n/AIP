import sqlite3
import logging
import os
from app.database import db_path

log_dir = "logs"
report_dir = "reports"

os.makedirs(log_dir, exist_ok=True)
os.makedirs(report_dir, exist_ok=True)

log_file_path = os.path.join(log_dir, "requests.log")
html_log_path = os.path.join(report_dir, "report.html")
html_final_report_path = os.path.join(report_dir, "final_report.html")


class HTMLHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        log_entry = self.format(record)
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(
                "<div style='margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;'>"
            )
            f.write(log_entry + "</div>\n")


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_handler = logging.FileHandler(log_file_path, encoding="utf-8")
log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(log_handler)

html_handler = HTMLHandler(html_log_path)
html_handler.setFormatter(
    logging.Formatter("<b>%(asctime)s</b> [%(levelname)s] %(message)s")
)
logger.addHandler(html_handler)


def generate_html_report():
    if not os.path.exists(log_file_path):
        logger.warning("Файл логов не найден для отчета.")
        return

    with open(log_file_path, "r", encoding="utf-8") as log_file:
        lines = log_file.readlines()

    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Лог-отчёт</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 20px; }
            h1 { text-align: center; }
            table { width: 100%; border-collapse: collapse; background-color: #fff; }
            th, td { padding: 10px; border: 1px solid #ccc; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .INFO { color: green; }
            .ERROR { color: red; }
            .WARNING { color: orange; }
        </style>
    </head>
    <body>
        <h1>Финальный отчёт логов</h1>
        <table>
            <tr><th>Время</th><th>Уровень</th><th>Сообщение</th></tr>
    """

    for line in lines:
        try:
            parts = line.strip().split(" ", 2)
            time, level, message = parts[0], parts[1].strip("[]"), parts[2]
            html_content += f"<tr><td>{time}</td><td class='{level}'>{level}</td><td>{message}</td></tr>"
        except Exception:
            continue

    html_content += """
        </table>
    </body>
    </html>
    """

    with open(html_final_report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"Финальный HTML-отчёт создан: {html_final_report_path}")


def add_user(user_id, username=None):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)
            """,
                (user_id, username),
            )
            conn.commit()
        logger.info(f"Пользователь с ID {user_id} и именем {username} добавлен.")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при добавлении пользователя с ID {user_id}: {e}")


def get_personal_holidays(user_id):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            SELECT holiday_name, holiday_date FROM personal_holidays WHERE user_id = ?
            """,
                (user_id,),
            )
            holidays = cursor.fetchall()
        logger.info(f"Получены праздники для пользователя с ID {user_id}.")
        return holidays
    except sqlite3.Error as e:
        logger.error(
            f"Ошибка при получении праздников для пользователя с ID {user_id}: {e}"
        )
        return []


def add_personal_holiday(user_id, holiday_name, holiday_date):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            INSERT INTO personal_holidays (user_id, holiday_name, holiday_date)
            VALUES (?, ?, ?)
            """,
                (user_id, holiday_name, holiday_date),
            )
            conn.commit()
        logger.info(
            f"Добавлен личный праздник '{holiday_name}' для пользователя с ID {user_id}."
        )
    except sqlite3.Error as e:
        logger.error(
            f"Ошибка при добавлении праздника '{holiday_name}' для пользователя с ID {user_id}: {e}"
        )


def delete_personal_holiday(user_id, holiday_name):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            DELETE FROM personal_holidays WHERE user_id = ? AND holiday_name = ?
            """,
                (user_id, holiday_name),
            )
            conn.commit()
        logger.info(
            f"Удалён праздник '{holiday_name}' для пользователя с ID {user_id}."
        )
    except sqlite3.Error as e:
        logger.error(
            f"Ошибка при удалении праздника '{holiday_name}' для пользователя с ID {user_id}: {e}"
        )


def delete_all_personal_holidays(user_id):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            DELETE FROM personal_holidays WHERE user_id = ?
            """,
                (user_id,),
            )
            conn.commit()
        logger.info(f"Удалены все праздники для пользователя с ID {user_id}.")
    except sqlite3.Error as e:
        logger.error(
            f"Ошибка при удалении всех праздников для пользователя с ID {user_id}: {e}"
        )


if __name__ == "__main__":
    generate_html_report()
