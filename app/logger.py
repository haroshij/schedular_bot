import logging
import sys

"""
Модуль для настройки логирования бота.

Логирование выполняется через стандартный модуль logging.
Можно менять уровень логов, формат, а также вывод в консоль и/или файл.

Использование:
    from app.logger import logger
    logger.info("Сообщение для лога")
"""

# Создаём объект логгера для нашего бота с уникальным именем
logger = logging.getLogger(
    "schedular_bot"
)  # Имя логгера, чтобы различать источники логов

# Устанавливаем уровень логирования
logger.setLevel(logging.INFO)

# Создаём форматтер для логов, чтобы сообщения были читабельными
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",  # Формат сообщения
    datefmt="%Y-%m-%d %H:%M:%S",  # Формат времени
)

# Создаём обработчик, который выводит логи в консоль (stdout)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)  # Применяем форматтер к обработчику
logger.addHandler(stream_handler)  # Добавляем обработчик к логгеру

# Можно раскомментировать, если нужен лог-файл
# file_handler = logging.FileHandler("bot.log", encoding="utf-8")
# file_handler.setFormatter(formatter)  # Применяем форматтер к файловому обработчику
# logger.addHandler(file_handler)  # Добавляем файловый обработчик к логгеру
