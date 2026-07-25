import os
import sys

# Add project root to path
sys.path.append("/Users/munisekhar/Desktop/swimTrackPro_v2")

from app import get_pg_connection
from datetime import datetime

try:
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, start_date, package, selected_days FROM bookings WHERE package IN ('Single', 'Demo')")
    rows = cursor.fetchall()
    
    updated_count = 0
    for row in rows:
        b_id, start_date_str, package, selected_days = row
        if not start_date_str: continue
        
        # handle multiple date formats if needed
        try:
            dt = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            # fallback if dates are stored differently
            continue
            
        correct_day = dt.strftime('%A')
        
        # selected_days might have trailing spaces or be a single day
        if str(selected_days).strip() != correct_day:
            print(f"Fixing booking {b_id}: {selected_days} -> {correct_day}")
            cursor.execute("UPDATE bookings SET selected_days = %s WHERE id = %s", (correct_day, b_id))
            updated_count += 1
            
    conn.commit()
    conn.close()
    print(f"Done! Fixed {updated_count} bookings.")
except Exception as e:
    print(f"Error: {e}")
