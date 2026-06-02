import sqlite3
import traceback

db_path = 'database.db'

try:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check existing columns in producttype
        cursor.execute('PRAGMA table_info(producttype)')
        columns = [row[1] for row in cursor.fetchall()]
        print('Columns in producttype:', columns)
        
        if 'unit' not in columns:
            print('Adding unit column to producttype...')
            cursor.execute('ALTER TABLE producttype ADD COLUMN unit VARCHAR DEFAULT "Piece" NOT NULL')
            print('Successfully added unit column to producttype.')
        else:
            print('unit column already exists in producttype.')
            
        # Check existing columns in product
        cursor.execute('PRAGMA table_info(product)')
        p_columns = [row[1] for row in cursor.fetchall()]
        print('Columns in product:', p_columns)
        
        if 'unit' not in p_columns:
            print('Adding unit column to product...')
            cursor.execute('ALTER TABLE product ADD COLUMN unit VARCHAR DEFAULT "Piece" NOT NULL')
            print('Successfully added unit column to product.')
        else:
            print('unit column already exists in product.')

        conn.commit()
except Exception as e:
    traceback.print_exc()
