import psycopg2
from config import DATABASE_URL

def test():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_name, current_login, previous_login FROM user_activity WHERE role = 'admin'")
    rows = cursor.fetchall()
    print("Admin Activity Rows:")
    for r in rows:
        print(r)
    conn.close()

if __name__ == '__main__':
    test()
