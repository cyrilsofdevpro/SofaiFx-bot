#!/usr/bin/env python
"""Initialize user preferences after database setup"""

from src.api.flask_app import app, db
from src.models import UserPreference, User

with app.app_context():
    user = User.query.filter_by(email='cyrilsofdev@gmail.com').first()
    
    if user:
        # Check if preferences exist
        pref = UserPreference.query.filter_by(user_id=user.id).first()
        
        if not pref:
            # Create new preferences
            pref = UserPreference(
                user_id=user.id,
                monitored_pairs=["EURUSD", "GBPUSD", "USDJPY"],
                execution_enabled=False
            )
            db.session.add(pref)
            db.session.commit()
            print(f'✅ UserPreference created for user {user.id}')
        else:
            print(f'✅ UserPreference already exists for user {user.id}')
    else:
        print('❌ User not found')
