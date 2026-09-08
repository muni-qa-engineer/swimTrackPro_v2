import sys
sys.path.append('.')
import psycopg2
from config import DATABASE_URL
print("Connecting to:", DATABASE_URL[:20] + "...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("SELECT username, is_approved FROM trainers WHERE username = 'admin'")
print("Admin in trainers table:", cur.fetchall())
