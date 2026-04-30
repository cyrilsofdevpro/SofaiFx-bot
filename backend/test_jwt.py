#!/usr/bin/env python
"""Test JWT token creation and validation"""

from flask_jwt_extended import create_access_token, decode_token, JWTManager
from flask import Flask
from datetime import timedelta

# Create Flask app with same config as main app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'sofai-fx-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 60 * 60 * 24 * 30

# Initialize JWT
jwt = JWTManager(app)

# Test token creation and validation
with app.app_context():
    print("🧪 Testing JWT Token Creation and Validation")
    print("=" * 50)
    
    # Create token
    token = create_access_token(identity=1, expires_delta=timedelta(days=30))
    print(f"✅ Token created: {token[:50]}...")
    
    # Decode token
    try:
        decoded = decode_token(token)
        print(f"✅ Token decoded successfully")
        print(f"   - Identity (user_id): {decoded.get('sub')}")
        print(f"   - Fresh: {decoded.get('fresh')}")
        print(f"   - Type: {decoded.get('type')}")
    except Exception as e:
        print(f"❌ Token decode error: {e}")
    
    # Now test with a request context
    print("\n🧪 Testing with Request Context")
    print("=" * 50)
    with app.test_request_context():
        token2 = create_access_token(identity=2, expires_delta=timedelta(days=30))
        print(f"✅ Token 2 created: {token2[:50]}...")
        
        try:
            decoded2 = decode_token(token2)
            print(f"✅ Token 2 decoded successfully")
            print(f"   - Identity (user_id): {decoded2.get('sub')}")
        except Exception as e:
            print(f"❌ Token 2 decode error: {e}")
