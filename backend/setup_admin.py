"""
Setup admin user for SofAi FX
This script makes the first user an admin
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models import db, User, init_db
from flask import Flask

# Create Flask app context
app = Flask(__name__)
db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(db_dir, 'sofai_fx.db').replace('\\', '/')
db_uri = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)

DEFAULT_ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'cyriladmin@gmail.com')
DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin1234')
DEFAULT_ADMIN_NAME = os.environ.get('ADMIN_NAME', 'Cyril Admin')


def setup_admin(email: str = DEFAULT_ADMIN_EMAIL, password: str = DEFAULT_ADMIN_PASSWORD, name: str = DEFAULT_ADMIN_NAME):
    """Create or promote an admin user by email."""
    with app.app_context():
        email = email.strip().lower()
        if not email or not password:
            print('❌ Admin email and password are required.')
            return

        user = User.query.filter_by(email=email).first()

        if user:
            user.is_admin = True
            user.is_active = True
            if not user.check_password(password):
                user.set_password(password)
                print('🔒 Existing admin password has been updated to the provided value.')
            db.session.commit()
            print(f"✅ Existing user '{user.name}' ({user.email}) is now an ADMIN")
        else:
            user = User(name=name, email=email, plan='enterprise', is_admin=True, is_active=True)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created admin user '{user.name}' ({user.email}) with admin access.")

        print('   Admin panel URL: http://localhost:8080/admin.html')
        print('   Use the credentials below to log in:')
        print(f'      Email: {email}')
        print(f'      Password: {password}')


if __name__ == '__main__':
    setup_admin()
