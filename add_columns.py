import sqlite3

try:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE notification ADD COLUMN notification_type VARCHAR;")
    cursor.execute("ALTER TABLE notification ADD COLUMN related_id INTEGER;")
    conn.commit()
    print("Columns added successfully")
except Exception as e:
    print(f"Error: {e}")
finally:
    if conn:
        conn.close()
