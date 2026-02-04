import os

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    print(f"TELEGRAM_TOKEN = {token}")

if __name__ == "__main__":
    main()