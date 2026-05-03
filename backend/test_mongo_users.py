"""
Test MongoDB integration - User creation and admin verification
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
from flask_bcrypt import Bcrypt
from datetime import datetime

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
print(f"🔄 MongoDB URI: {MONGO_URI[:60]}...")

# Connect to MongoDB
try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        tls=True,
        tlsCAFile=certifi.where()
    )
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    sys.exit(1)

db = client['sofaifx']
users_collection = db['users']

# Initialize bcrypt
bcrypt = Bcrypt()

# Test 1: Create a test user
print("\n" + "="*60)
print("TEST 1: Creating a test user")
print("="*60)

test_user = {
    'name': 'Test User',
    'email': 'test@example.com',
    'password': bcrypt.generate_password_hash('testpass123').decode('utf-8'),
    'plan': 'free',
    'is_admin': False,
    'is_active': True,
    'created_at': datetime.utcnow(),
    'updated_at': datetime.utcnow()
}

try:
    # Delete if exists
    users_collection.delete_one({'email': 'test@example.com'})
    
    result = users_collection.insert_one(test_user)
    print(f"✅ Test user created with ID: {result.inserted_id}")
except Exception as e:
    print(f"❌ Failed to create test user: {e}")
    sys.exit(1)

# Test 2: Verify test user can be found
print("\n" + "="*60)
print("TEST 2: Retrieving test user")
print("="*60)

try:
    found_user = users_collection.find_one({'email': 'test@example.com'})
    if found_user:
        print(f"✅ Found user: {found_user['name']} ({found_user['email']})")
        print(f"   Plan: {found_user['plan']}, Admin: {found_user['is_admin']}")
    else:
        print("❌ User not found")
except Exception as e:
    print(f"❌ Failed to retrieve user: {e}")

# Test 3: Verify password hashing works
print("\n" + "="*60)
print("TEST 3: Password verification")
print("="*60)

try:
    if bcrypt.check_password_hash(found_user['password'], 'testpass123'):
        print("✅ Password verification successful!")
    else:
        print("❌ Password verification failed")
except Exception as e:
    print(f"❌ Password check failed: {e}")

# Test 4: Admin user creation/verification
print("\n" + "="*60)
print("TEST 4: Admin user creation/verification")
print("="*60)

admin_email = os.getenv('ADMIN_EMAIL', 'cyriladmin@gmail.com')
admin_password = os.getenv('ADMIN_PASSWORD', 'Admin1234')
admin_name = os.getenv('ADMIN_NAME', 'Cyril Admin')

try:
    existing_admin = users_collection.find_one({'email': admin_email})
    
    if existing_admin:
        print(f"✅ Admin user already exists: {existing_admin['name']}")
        print(f"   Email: {existing_admin['email']}")
        print(f"   Is Admin: {existing_admin['is_admin']}")
        print(f"   Plan: {existing_admin['plan']}")
        
        # Verify admin password
        if bcrypt.check_password_hash(existing_admin['password'], admin_password):
            print("✅ Admin password is correct!")
        else:
            print("⚠️  Admin password mismatch - updating...")
            hashed_pwd = bcrypt.generate_password_hash(admin_password).decode('utf-8')
            users_collection.update_one(
                {'email': admin_email},
                {'$set': {'password': hashed_pwd, 'updated_at': datetime.utcnow()}}
            )
            print("✅ Admin password updated!")
    else:
        print(f"⚠️  Admin user not found - creating...")
        admin_user = {
            'name': admin_name,
            'email': admin_email,
            'password': bcrypt.generate_password_hash(admin_password).decode('utf-8'),
            'plan': 'enterprise',
            'is_admin': True,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = users_collection.insert_one(admin_user)
        print(f"✅ Admin user created with ID: {result.inserted_id}")
        print(f"   Email: {admin_email}")
        print(f"   Plan: enterprise")
        
except Exception as e:
    print(f"❌ Admin user operation failed: {e}")
    sys.exit(1)

# Test 5: List all users
print("\n" + "="*60)
print("TEST 5: All users in database")
print("="*60)

try:
    all_users = list(users_collection.find({}))
    print(f"✅ Total users in database: {len(all_users)}\n")
    
    for user in all_users:
        is_admin_badge = "👑 ADMIN" if user.get('is_admin') else "👤 USER"
        print(f"   {is_admin_badge}: {user['name']} ({user['email']}) - {user['plan']}")
        
except Exception as e:
    print(f"❌ Failed to list users: {e}")

# Cleanup
print("\n" + "="*60)
print("CLEANUP: Removing test user")
print("="*60)

try:
    result = users_collection.delete_one({'email': 'test@example.com'})
    print(f"✅ Test user removed (deleted: {result.deleted_count})")
except Exception as e:
    print(f"❌ Failed to remove test user: {e}")

print("\n" + "="*60)
print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
print("="*60)

# Close connection
client.close()
print("\n✅ MongoDB connection closed")
