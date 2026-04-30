#!/usr/bin/env python3
import sqlite3
import os

db_path = 'sofai_fx.db'

if not os.path.exists(db_path):
    print(f"❌ Database {db_path} does not exist")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check if users table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cur.fetchone():
        print("❌ Users table does not exist")
        exit(1)
    
    # Get column info
    cur.execute("PRAGMA table_info(users)")
    columns = cur.fetchall()
    
    print("✓ Users table columns:")
    col_names = [col[1] for col in columns]
    for col in columns:
        print(f"  • {col[1]}: {col[2]}")
    
    # Check if is_admin exists
    if 'is_admin' in col_names:
        print("\n✅ is_admin column EXISTS")
    else:
        print("\n❌ is_admin column MISSING")
        print(f"   Available columns: {', '.join(col_names)}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
