import sys
import os
from datetime import datetime

# Ensure current directory is in python path
sys.path.append(os.getcwd())

from sqlalchemy import inspect, text
from app.database import engine
from app.models import SQLModel

def run_migrations():
    """
    Automatically inspects the database schema and adds any missing columns 
    defined in SQLModel classes. Supports both SQLite (local) and PostgreSQL (Render).
    """
    dialect_name = engine.dialect.name
    print(f"\n--- [DB MIGRATION] Starting schema sync on database engine: '{dialect_name}' ---")
    
    inspector = inspect(engine)
    
    with engine.begin() as connection:
        migrations_performed = 0
        
        for table_name, table in SQLModel.metadata.tables.items():
            # Check if table exists in the database
            if not inspector.has_table(table_name):
                print(f"[DB MIGRATION] Table '{table_name}' does not exist yet. It will be created by SQLModel.create_all().")
                continue
                
            # Get existing columns in the database
            existing_cols = {col['name'] for col in inspector.get_columns(table_name)}
            
            # Check for missing columns defined in SQLModel
            for col in table.columns:
                if col.name not in existing_cols:
                    type_ddl = str(col.type.compile(dialect=engine.dialect))
                    col_name = col.name.lower()
                    
                    # 1. Compile ALTER TABLE statement
                    alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {type_ddl}"
                    
                    # 2. Determine default value to populate existing NULL rows
                    post_update_val = None
                    if col_name in ("created_at", "updated_at") or "DATETIME" in type_ddl or "TIMESTAMP" in type_ddl:
                        post_update_val = datetime.utcnow()
                    elif col_name == "unit":
                        post_update_val = "Piece"
                    elif col.default is not None:
                        if hasattr(col.default, 'arg'):
                            val = col.default.arg
                            if callable(val):
                                if "DATETIME" in type_ddl or "TIMESTAMP" in type_ddl:
                                    post_update_val = datetime.utcnow()
                            else:
                                post_update_val = val
                    else:
                        if not col.nullable:
                            if "INT" in type_ddl or "INTEGER" in type_ddl:
                                post_update_val = 0
                            elif "FLOAT" in type_ddl or "NUMERIC" in type_ddl or "REAL" in type_ddl:
                                post_update_val = 0.0
                            elif "BOOL" in type_ddl:
                                post_update_val = False
                            elif "VARCHAR" in type_ddl or "CHAR" in type_ddl or "TEXT" in type_ddl:
                                post_update_val = ""
                    
                    # Execute ALTER TABLE
                    print(f"[DB MIGRATION] Table '{table_name}': Adding column '{col.name}' ({type_ddl}) via: {alter_stmt}")
                    try:
                        connection.execute(text(alter_stmt))
                    except Exception as e:
                        # Some dialects or database setups might have issues, log it and raise to roll back transaction
                        print(f"[DB MIGRATION] ERROR executing alter statement: {alter_stmt}\nError details: {e}")
                        raise e
                    
                    # Backfill existing rows if default value is specified
                    if post_update_val is not None:
                        update_stmt = f"UPDATE {table_name} SET {col.name} = :val WHERE {col.name} IS NULL"
                        print(f"[DB MIGRATION] Table '{table_name}': Updating existing rows for '{col.name}'...")
                        try:
                            connection.execute(text(update_stmt), {"val": post_update_val})
                        except Exception as e:
                            print(f"[DB MIGRATION] ERROR executing update statement: {update_stmt}\nError details: {e}")
                            raise e
                            
                    migrations_performed += 1
                    
        if migrations_performed > 0:
            print(f"[DB MIGRATION] Migration completed successfully. Synchronized {migrations_performed} column(s).\n")
        else:
            print("[DB MIGRATION] Database schema is fully up to date. No migration needed.\n")

if __name__ == '__main__':
    run_migrations()
