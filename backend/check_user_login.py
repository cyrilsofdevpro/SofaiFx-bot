#!/usr/bin/env python3
"""Check and create user account if needed"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from src.models import db, User
from src.api.flask_app import app

# Initialize database
with app.app_context():
    # Check if user exists
    user = User.query.filter_by(email='cyrilsofdev@gmail.com').first()
    
    if user:
        print(f"✅ User found: {user.name} ({user.email})")
        print(f"   Active: {user.is_active}")
        print(f"   ID: {user.id}")
        
        # Test password
        if user.check_password('passwoed1234'):
            print(f"✅ Password is CORRECT")
        else:
            print(f"❌ Password is WRONG - resetting...")
            user.set_password('passwoed1234')
            db.session.commit()
            print(f"✅ Password reset to: passwoed1234")
    else:
        print("❌ User NOT found")
        print("📝 Creating user account...")
        
        # Create new user
        new_user = User(name='Cyril', email='cyrilsofdev@gmail.com', plan='premium')
        new_user.set_password('passwoed1234')
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f"✅ User created successfully!")
        print(f"   Email: cyrilsofdev@gmail.com")
        print(f"   Password: passwoed1234")
        print(f"   ID: {new_user.id}")
        print(f"   Active: {new_user.is_active}")
