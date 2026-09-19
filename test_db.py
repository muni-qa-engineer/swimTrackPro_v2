from swimtrackpro.runtime import get_pg_connection

def run():
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, name FROM trainers")
    print("Trainers:", cursor.fetchall())
    
    cursor.execute("SELECT id, owner_phone, trainer_username, completed_classes, is_completed FROM bookings")
    print("Bookings:", cursor.fetchall())
    
    conn.close()

if __name__ == '__main__':
    from app import app
    with app.app_context():
        run()
