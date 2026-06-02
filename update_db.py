import sqlite3
import sys
import os
import shutil
from datetime import datetime

# Ensure the current workspace is in python path to import app modules
sys.path.append(os.getcwd())

from app.models import SQLModel

db_path = 'database.db'
backup_path = 'database.db.backup'

def backup_database():
    if os.path.exists(db_path):
        print(f"Creating database backup at {backup_path}...")
        shutil.copy2(db_path, backup_path)
        print("Backup created successfully.")

def get_sqlite_type_and_default(column):
    """
    Map SQLAlchemy/SQLModel column to SQLite type, default clause for ALTER,
    and Python value to populate existing NULL rows.
    """
    col_type = str(column.type).upper()
    col_name = column.name.lower()
    
    # 1. Type mapping
    sqlite_type = "VARCHAR"
    if "DATETIME" in col_type or "TIMESTAMP" in col_type:
        sqlite_type = "DATETIME"
    elif "INTEGER" in col_type or "INT" in col_type:
        sqlite_type = "INTEGER"
    elif "BOOLEAN" in col_type or "BOOL" in col_type:
        sqlite_type = "BOOLEAN"
    elif "FLOAT" in col_type or "NUMERIC" in col_type or "REAL" in col_type:
        sqlite_type = "FLOAT"
        
    # 2. Default mapping
    default_clause = ""
    post_update_val = None
    
    # Specific defaults based on column name or type
    if col_name in ("created_at", "updated_at") or sqlite_type == "DATETIME":
        # SQLite ALTER TABLE does not allow dynamic defaults like CURRENT_TIMESTAMP.
        # We will not specify a default in DDL, but populate existing rows with python update.
        post_update_val = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    elif col_name == "unit":
        default_clause = "DEFAULT 'Piece'"
        post_update_val = "Piece"
    elif column.default is not None:
        if hasattr(column.default, 'arg'):
            val = column.default.arg
            if callable(val):
                if sqlite_type == "DATETIME":
                    post_update_val = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            else:
                if isinstance(val, str):
                    default_clause = f"DEFAULT '{val}'"
                elif isinstance(val, bool):
                    default_clause = f"DEFAULT {1 if val else 0}"
                else:
                    default_clause = f"DEFAULT {val}"
                post_update_val = val
    else:
        # Sensible defaults for non-nullable columns to avoid None validation issues in Pydantic
        if not column.nullable:
            if sqlite_type == "INTEGER":
                default_clause = "DEFAULT 0"
                post_update_val = 0
            elif sqlite_type == "FLOAT":
                default_clause = "DEFAULT 0.0"
                post_update_val = 0.0
            elif sqlite_type == "BOOLEAN":
                default_clause = "DEFAULT 0"
                post_update_val = False
            elif sqlite_type == "VARCHAR":
                default_clause = "DEFAULT ''"
                post_update_val = ""
                
    return sqlite_type, default_clause, post_update_val

def migrate():
    backup_database()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n--- Starting SQLModel-driven SQLite Schema Migration ---")
    
    migrations_performed = 0
    
    for table_name, table in SQLModel.metadata.tables.items():
        # Check if table exists in SQLite
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f"Table '{table_name}' does not exist in SQLite database. It will be created by SQLModel.create_all().")
            continue
            
        # Get existing columns in SQLite
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        # Check columns defined in SQLModel
        for col in table.columns:
            if col.name not in existing_cols:
                sqlite_type, default_clause, post_update_val = get_sqlite_type_and_default(col)
                
                alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {sqlite_type}"
                if default_clause:
                    alter_stmt += f" {default_clause}"
                    
                print(f"Table '{table_name}': Adding column '{col.name}' ({sqlite_type}) via: {alter_stmt}")
                try:
                    cursor.execute(alter_stmt)
                    
                    # Update existing rows if necessary
                    if post_update_val is not None:
                        update_stmt = f"UPDATE {table_name} SET {col.name} = ? WHERE {col.name} IS NULL"
                        cursor.execute(update_stmt, (post_update_val,))
                        print(f"Table '{table_name}': Updated existing rows for '{col.name}' with default value.")
                        
                    migrations_performed += 1
                except Exception as e:
                    print(f"ERROR executing: {alter_stmt}\nReason: {e}")
                    conn.rollback()
                    conn.close()
                    sys.exit(1)
                    
    if migrations_performed > 0:
        conn.commit()
        print(f"\nMigration completed successfully. Performed {migrations_performed} column addition(s).")
    else:
        print("\nNo database schema discrepancies found. Database is up to date.")
        
    conn.close()

if __name__ == '__main__':
    migrate()
