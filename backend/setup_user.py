#!/usr/bin/env python
"""Setup user account after database recreation"""

from src.api.flask_app import app, db
from src.models import User

with app.app_context():
    # Create user
    user = User(name='Cyril', email='cyrilsofdev@gmail.com', plan='premium', is_active=True)
    user.set_password('passwoed1234')
    db.session.add(user)
    db.session.commit()
    print(f'✅ User created: {user.email} (ID: {user.id})')
