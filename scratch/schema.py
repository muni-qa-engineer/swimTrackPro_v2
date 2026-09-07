import psycopg2
from config import DATABASE_URL
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'user_activity'")
for row in cursor.fetchall(): print(row)
