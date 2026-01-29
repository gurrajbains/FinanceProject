from database import get_connection

def main():
    conn = get_connection()
    conn.close()
    print("Connection OK")

if __name__ == "__main__":
    main()
