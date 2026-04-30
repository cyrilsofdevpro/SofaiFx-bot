#!/usr/bin/env python3
"""
Setup test users with known passwords
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.flask_app import app
from src.models import db, User

print("Setting up test users...\n")

with app.app_context():
    # Define test users
    test_users = [
        {'email': 'user1@gmail.com', 'name': 'User One', 'password': 'user1123'},
        {'email': 'user3@gmail.com', 'name': 'User Three', 'password': 'user3123'},
        {'email': 'bro@gmail.com', 'name': 'bro', 'password': 'bro123'},
    ]
    
    for user_data in test_users:
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if existing_user:
            # Update password using set_password for proper bcrypt
            existing_user.set_password(user_data['password'])
            print(f"✅ Updated {user_data['email']} with password: {user_data['password']}")
        else:
            # Create new user
            new_user = User(
                email=user_data['email'],
                name=user_data['name'],
            )
            new_user.set_password(user_data['password'])
            db.session.add(new_user)
            print(f"✅ Created {user_data['email']} with password: {user_data['password']}")
    
    db.session.commit()
    print("\n✅ All users setup complete!")
    
    # Show all users
    print("\nCurrent users in database:")
    for user in User.query.all():
        signals_count = db.session.query(db.func.count()).select_from(db.session.query(db.func.count()).from_statement(
            "SELECT * FROM signals WHERE user_id = :uid"
        ).params(uid=user.id)).scalar() if False else 0
        print(f"  • {user.email} ({user.name})")
