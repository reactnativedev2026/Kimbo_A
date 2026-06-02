import sys
import os

# Ensure the current workspace is in python path
sys.path.append(os.getcwd())

from app.migrations import run_migrations

if __name__ == '__main__':
    run_migrations()
