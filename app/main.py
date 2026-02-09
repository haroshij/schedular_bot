from dotenv import load_dotenv
from bot.app import create_app
from app.logger import logger

def main():
    load_dotenv()
    try:
        logger.info('Запуск бота...')
        app = create_app()
        app.run_polling()
    except Exception as e:
        logger.exception("Ошибка при запуске бота\n%s", e)
        raise

if __name__ == "__main__":
    main()
