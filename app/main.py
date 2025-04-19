import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from app.handlers import router
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

log_file_path = os.path.join(log_dir, "main.log")

report_dir = "reports"
os.makedirs(report_dir, exist_ok=True)

html_report_path = os.path.join(report_dir, "report.html")
html_final_report_path = os.path.join(report_dir, "final_report.html")


class HTMLHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        try:
            log_entry = self.format(record)
            with open(self.filename, "a", encoding="utf-8") as f:
                f.write(log_entry + "<br>\n")
        except Exception:
            self.handleError(record)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

html_handler = HTMLHandler(html_report_path)
html_handler.setLevel(logging.INFO)
html_handler.setFormatter(
    logging.Formatter("<b>%(asctime)s</b> [%(levelname)s] <i>%(name)s</i>: %(message)s")
)
logging.getLogger().addHandler(html_handler)

logger = logging.getLogger(__name__)


def generate_html_report():
    if not os.path.exists(log_file_path):
        logger.warning("Лог файл не найден для отчета.")
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


async def main():
    logger.info("Запуск бота...")

    bot = Bot(token="7245211358:AAGzWgl_D-OpRvTT1l5VBHE9_HJM8IOSbLs")
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Роутеры подключены. Бот начинает polling.")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Ошибка во время polling:")
    finally:
        logger.info("Polling завершён.")
        generate_html_report()


if __name__ == "__main__":
    asyncio.run(main())
