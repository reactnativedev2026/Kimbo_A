import os
import json
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Set path context
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.backup import run_backup

if __name__ == "__main__":
    print("=========================================")
    print("Starting SBBMS Database Backup Procedure")
    print("=========================================")
    result = run_backup()
    print("\nResult:")
    print(json.dumps(result, indent=2))
    print("=========================================")
