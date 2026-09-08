import sys
sys.path.append('.')
import psycopg2
from config import DATABASE_URL
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("SELECT id, author_type, author_name, message FROM notices LIMIT 5")
print("Notices:", cur.fetchall())
