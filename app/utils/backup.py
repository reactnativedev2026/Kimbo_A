import os
import gzip
import shutil
import subprocess
import logging
from datetime import datetime, date
import tempfile
import cloudinary
import cloudinary.uploader
from sqlmodel import text
from sqlalchemy import create_engine, inspect

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DBBackup")

def json_serializer(obj):
    """Custom JSON serializer for dates, datetimes, and enums."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "value"):  # Handles Enums
        return obj.value
    raise TypeError(f"Type {type(obj)} is not serializable")

def fallback_json_backup(db_url: str, output_path: str):
    """Fallback database backup: queries all tables and serializes data to a JSON file."""
    logger.info("Starting Python-based fallback backup...")
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    backup_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": "PostgreSQL" if db_url.startswith("postgres") else "SQLite",
        "tables": {}
    }
    
    with engine.connect() as conn:
        for table in tables:
            logger.info(f"Backing up table: {table}")
            try:
                # Query all columns and rows from table
                result = conn.execute(text(f'SELECT * FROM "{table}"'))
                columns = list(result.keys())
                rows = []
                for row in result:
                    row_dict = {}
                    for col, val in zip(columns, row):
                        row_dict[col] = val
                    rows.append(row_dict)
                backup_data["tables"][table] = rows
            except Exception as e:
                logger.error(f"Error backing up table {table}: {e}")
                
    import json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, default=json_serializer, indent=2)
    logger.info("Fallback JSON backup completed.")

def run_backup():
    """Main backup procedure: backs up DB, compresses it, and uploads to Cloudinary."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is not set.")
        return {"status": "failed", "error": "DATABASE_URL not set"}

    # Cloudinary Config
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not all([cloud_name, api_key, api_secret]):
        logger.error("Cloudinary credentials are not completely set in the environment.")
        return {"status": "failed", "error": "Cloudinary credentials missing"}

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )

    now = datetime.now()
    date_folder = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%H-%M-%S")
    
    # We will use temporary directories for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        raw_backup_path = os.path.join(temp_dir, "db_backup")
        gzip_backup_path = os.path.join(temp_dir, f"backup_{timestamp}.gz")
        
        is_pg_dump_success = False
        
        # Only try pg_dump if we are using PostgreSQL
        if db_url.startswith("postgresql") or db_url.startswith("postgres"):
            logger.info("Attempting pg_dump backup...")
            sql_backup_path = raw_backup_path + ".sql"
            try:
                # Run pg_dump command
                process = subprocess.run(
                    ["pg_dump", f"--dbname={db_url}", "-F", "p", "-f", sql_backup_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if process.returncode == 0:
                    raw_backup_path = sql_backup_path
                    is_pg_dump_success = True
                    logger.info("pg_dump backup completed successfully.")
                else:
                    logger.warning(f"pg_dump exited with error code {process.returncode}: {process.stderr}")
            except Exception as e:
                logger.warning(f"Could not run pg_dump: {e}")
        
        # Fallback if pg_dump was not successful
        if not is_pg_dump_success:
            json_backup_path = raw_backup_path + ".json"
            try:
                fallback_json_backup(db_url, json_backup_path)
                raw_backup_path = json_backup_path
            except Exception as e:
                logger.error(f"Fallback backup failed: {e}")
                return {"status": "failed", "error": f"Backup generation failed: {e}"}

        # Compress backup file with Gzip
        logger.info("Compressing backup file...")
        try:
            with open(raw_backup_path, "rb") as f_in:
                with gzip.open(gzip_backup_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logger.info("Backup compression completed.")
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return {"status": "failed", "error": f"Compression failed: {e}"}

        # Upload to Cloudinary
        logger.info("Uploading backup to Cloudinary...")
        file_extension = "sql.gz" if is_pg_dump_success else "json.gz"
        public_id = f"db_backups/{date_folder}/backup_{timestamp}"
        
        try:
            upload_result = cloudinary.uploader.upload(
                gzip_backup_path,
                resource_type="raw",
                public_id=public_id,
                unique_filename=False,
                overwrite=True
            )
            secure_url = upload_result.get("secure_url")
            logger.info(f"Database backup uploaded successfully to: {secure_url}")
            return {
                "status": "success",
                "message": "Database backup completed successfully",
                "filename": f"backup_{timestamp}.{file_extension}",
                "cloudinary_url": secure_url,
                "backup_method": "pg_dump" if is_pg_dump_success else "python_fallback",
                "timestamp": now.isoformat()
            }
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            return {"status": "failed", "error": f"Cloudinary upload failed: {e}"}
