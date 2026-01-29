# main.py
from database import init_db


def main():
    """
    Application entry point.
    """
    init_db()
    print("Finance Tracker base structure loaded")


if __name__ == "__main__":
    main()
