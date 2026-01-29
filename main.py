# main.py
from database import init_db


def main():
    """
    Application entry point.
    """
    init_db()
    print("DB has been initialized.")


if __name__ == "__main__":
    main()
