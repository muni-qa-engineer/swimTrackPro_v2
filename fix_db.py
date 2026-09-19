from swimtrackpro.runtime import get_pg_connection

def run():
    conn = get_pg_connection()
    cursor = conn.cursor()
    
    try:
        # Check if pros/cons exist
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='coach_feedback' AND column_name='pros'")
        if cursor.fetchone():
            cursor.execute("ALTER TABLE coach_feedback RENAME COLUMN pros TO comment")
            cursor.execute("ALTER TABLE coach_feedback DROP COLUMN cons")
            conn.commit()
            print("Renamed pros to comment and dropped cons.")
            
        # Add Unique constraint
        cursor.execute("ALTER TABLE coach_feedback ADD CONSTRAINT unique_user_coach UNIQUE (trainer_username, guest_phone)")
        conn.commit()
        print("Added unique constraint.")
    except Exception as e:
        conn.rollback()
        print(f"Error (might already be applied or duplicate data exists): {e}")
        
        # If there are duplicates, we need to delete them.
        if 'could not create unique index' in str(e).lower() or 'duplicate key' in str(e).lower():
            print("Deleting duplicate reviews keeping the latest one...")
            cursor.execute("""
                DELETE FROM coach_feedback 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM coach_feedback 
                    GROUP BY trainer_username, guest_phone
                )
            """)
            conn.commit()
            cursor.execute("ALTER TABLE coach_feedback ADD CONSTRAINT unique_user_coach UNIQUE (trainer_username, guest_phone)")
            conn.commit()
            print("Duplicates deleted and unique constraint added.")

    conn.close()

if __name__ == '__main__':
    run()
