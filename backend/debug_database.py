#!/usr/bin/env python3
"""
Debug script to check database state directly
Run this from the backend directory: python debug_database.py
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models import db, Signal, User, init_db
from src.api.flask_app import app
from src.utils.logger import logger

def check_database():
    """Check database state"""
    print("\n" + "="*60)
    print("📊 DATABASE DEBUG REPORT")
    print("="*60)
    
    with app.app_context():
        # Check database file
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        db_exists = os.path.exists(db_path)
        
        print(f"\n📁 DATABASE FILE")
        print(f"  Path: {db_path}")
        print(f"  Exists: {db_exists}")
        if db_exists:
            size = os.path.getsize(db_path)
            print(f"  Size: {size} bytes ({size/1024:.2f} KB)")
        
        # Check tables
        print(f"\n📋 TABLES")
        inspector = __import__('sqlalchemy').inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"  Tables found: {tables}")
        
        # Check users
        print(f"\n👥 USERS")
        users = User.query.all()
        print(f"  Total: {len(users)}")
        for user in users:
            print(f"    - ID: {user.id}, Email: {user.email}, Name: {user.name}")
        
        # Check signals
        print(f"\n📊 SIGNALS")
        signals = Signal.query.all()
        print(f"  Total: {len(signals)}")
        
        if len(signals) == 0:
            print("  ⚠️ No signals in database!")
        else:
            # Group by user
            signals_by_user = {}
            for sig in signals:
                if sig.user_id not in signals_by_user:
                    signals_by_user[sig.user_id] = []
                signals_by_user[sig.user_id].append(sig)
            
            for user_id in signals_by_user:
                print(f"\n  User ID {user_id}:")
                for sig in signals_by_user[user_id]:
                    print(f"    - {sig.symbol} {sig.signal_type} @ {sig.created_at} (confidence: {sig.confidence:.2f})")
        
        print("\n" + "="*60)
        print("✅ Database check complete\n")

if __name__ == '__main__':
    try:
        check_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
