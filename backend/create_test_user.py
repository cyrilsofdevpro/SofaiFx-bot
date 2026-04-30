#!/usr/bin/env python
"""Create test user for frontend login"""

import sys
sys.path.insert(0, '.')

from src.models import db, User
from src.api.flask_app import app

with app.app_context():
    # Check if user exists
    user = User.query.filter_by(email='trader@sofai.com').first()
    if not user:
        user = User(
            name='Test Trader',
            email='trader@sofai.com'
        )
        user.set_password('Trader@123')
        db.session.add(user)
        db.session.commit()
        print(f"User created: {user.email}, ID: {user.id}")
    else:
        print(f"User exists: {user.email}, ID: {user.id}")
