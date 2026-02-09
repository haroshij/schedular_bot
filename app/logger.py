import logging
import sys

# Создаём логгер
logger = logging.getLogger("schedular_bot")
logger.setLevel(logging.INFO)  # DEBUG для разработки, INFO для продакшена

# Формат логов
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Поток в stdout
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# При желании можно добавить файл
# file_handler = logging.FileHandler("bot.log", encoding="utf-8")
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
