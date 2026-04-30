"""
Setup admin user for SofAi FX
This script makes the first user an admin
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models import db, User, init_db
from src.config import config
from flask import Flask

# Create Flask app context
app = Flask(__name__)
db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(db_dir, 'sofai_fx.db').replace('\\', '/')
db_uri = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)

def setup_admin():
    """Set first user as admin"""
    with app.app_context():
        # Get first user
        first_user = User.query.order_by(User.created_at.asc()).first()
        
        if not first_user:
            print("❌ No users found. Please create a user first.")
            return
        
        # Make them admin
        first_user.is_admin = True
        db.session.commit()
        
        print(f"✅ User '{first_user.name}' ({first_user.email}) is now an ADMIN")
        print(f"   You can now access: http://localhost:8080/admin.html")

if __name__ == '__main__':
    setup_admin()
