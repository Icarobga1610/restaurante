#!/usr/bin/env python3
"""Backup script for SQLite database."""
import shutil
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "restaurante.db")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "backups")


def backup():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"restaurante_backup_{timestamp}.db")

    shutil.copy2(DB_PATH, backup_path)
    size_mb = os.path.getsize(backup_path) / (1024 * 1024)
    print(f"✅ Backup created: {backup_path} ({size_mb:.2f} MB)")


def list_backups():
    if not os.path.exists(BACKUP_DIR):
        print("No backups found.")
        return

    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")],
        reverse=True,
    )
    print(f"Backups ({len(backups)}):")
    for b in backups:
        path = os.path.join(BACKUP_DIR, b)
        size = os.path.getsize(path) / (1024 * 1024)
        print(f"  - {b} ({size:.2f} MB)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_backups()
    else:
        backup()
