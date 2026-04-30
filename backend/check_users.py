#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.flask_app import app
from src.models import db, User, Signal

with app.app_context():
    print("\n📋 CURRENT USERS:")
    users = User.query.all()
    for user in users:
        signals_count = Signal.query.filter_by(user_id=user.id).count()
        print(f"  ID {user.id}: {user.email} ({user.name}) - {signals_count} signals")
