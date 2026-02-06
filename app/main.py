from dotenv import load_dotenv
from bot.app import create_app

def main():
    load_dotenv()
    app = create_app()
    app.run_polling()

if __name__ == "__main__":
    main()
