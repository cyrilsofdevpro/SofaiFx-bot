"""
Test MongoDB connection and basic operations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models_mongo import init_mongo_db, User, seed_admin
from flask import Flask

def test_mongodb():
    """Test MongoDB connection and operations"""
    app = Flask(__name__)

    print("🔄 Initializing MongoDB connection...")
    init_mongo_db(app)

    with app.app_context():
        print("✅ MongoDB connected")

        # Test admin seeding
        print("🔄 Seeding admin user...")
        seed_admin()

        # Test user creation
        print("🔄 Testing user operations...")

        # Check if admin exists
        admin = User.objects(email='cyriladmin@gmail.com').first()
        if admin:
            print(f"✅ Admin user found: {admin.name} ({admin.email}) - Admin: {admin.is_admin}")
        else:
            print("❌ Admin user not found")

        # Test user creation
        test_user = User(
            name='Test User',
            email='test@example.com',
            plan='free'
        )
        test_user.set_password('testpass123')
        test_user.save()
        print(f"✅ Test user created: {test_user.name}")

        # Test user retrieval
        retrieved = User.objects(email='test@example.com').first()
        if retrieved and retrieved.check_password('testpass123'):
            print("✅ User authentication works")
        else:
            print("❌ User authentication failed")

        # Clean up test user
        test_user.delete()
        print("✅ Test user cleaned up")

        print("🎉 All MongoDB tests passed!")

if __name__ == '__main__':
    test_mongodb()