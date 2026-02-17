"""
Модуль для настройки логирования бота.
Логирование выполняется через стандартный модуль logging.
Можно менять уровень логов, формат, а также вывод в консоль и/или файл.
"""

import sys
import logging

# Создаём объект логгера для нашего бота с уникальным именем
logger = logging.getLogger("schedular_bot")
logger.setLevel(logging.INFO)

# Создаём форматтер для логов
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Создаём обработчик, который выводит логи в консоль (stdout)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)  # Добавляем обработчик к логгеру

# Можно раскомментировать, если нужен лог-файл
# file_handler = logging.FileHandler("bot.log", encoding="utf-8")
# file_handler.setFormatter(formatter)  # Применяем форматтер к файловому обработчику
# logger.addHandler(file_handler)  # Добавляем файловый обработчик к логгеру
