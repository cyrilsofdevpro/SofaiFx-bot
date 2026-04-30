# 🔐 SofAi FX - User Authentication System

## Overview

SofAi FX now includes a complete **user authentication system** with JWT tokens, allowing users to:
- ✅ Create accounts
- ✅ Login securely
- ✅ Access protected dashboard
- ✅ Manage their trading signals

---

## 🎯 Features

### User Registration
- Email and password validation
- Secure password hashing with bcrypt
- Plan assignment (free, premium, enterprise)
- Account creation tracking

### User Login
- Email/password verification
- JWT token generation (30-day expiration)
- Session management
- Account status checking

### Protected Routes
- `/auth/me` - Get current user info
- `/api/signals` - Requires valid JWT token
- `/api/analyze` - Requires valid JWT token

### Additional Features
- Change password endpoint
- Logout functionality
- User profile management

---

## 📋 Database Structure

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    plan VARCHAR(20) DEFAULT 'free',
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE
);
```

**Columns:**
- `id` - Primary key
- `email` - Unique user email
- `password` - Bcrypt hashed password
- `plan` - Subscription plan (free/premium/enterprise)
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp
- `is_active` - Account status

---

## 🔑 API Endpoints

### 1. Register User

**Endpoint:** `POST /auth/register`

**Request:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

**Response (201):**
```json
{
    "message": "Registration successful",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "plan": "free",
        "created_at": "2026-04-24T02:19:01.236243",
        "is_active": true
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 2. Login User

**Endpoint:** `POST /auth/login`

**Request:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

**Response (200):**
```json
{
    "message": "Login successful",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "plan": "free",
        "created_at": "2026-04-24T02:19:01.236243",
        "is_active": true
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 3. Get Current User

**Endpoint:** `GET /auth/me`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
    "user": {
        "id": 1,
        "email": "user@example.com",
        "plan": "free",
        "created_at": "2026-04-24T02:19:01.236243",
        "is_active": true
    }
}
```

---

### 4. Change Password

**Endpoint:** `POST /auth/change-password`

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
    "current_password": "oldpassword123",
    "new_password": "newpassword456"
}
```

**Response (200):**
```json
{
    "message": "Password changed successfully"
}
```

---

### 5. Logout

**Endpoint:** `POST /auth/logout`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
    "message": "Logged out successfully"
}
```

---

## 🛡️ JWT Token Structure

**Token Format:** `Header.Payload.Signature`

**Payload Example:**
```json
{
    "fresh": false,
    "iat": 1776997141,
    "jti": "770c8be6-4854-4879-afe2-d16aadb3d544",
    "type": "access",
    "sub": 1,              // User ID
    "nbf": 1776997141,     // Not before
    "exp": 1779589141      // Expires in 30 days
}
```

**Token Expiration:** 30 days from generation

---

## 🔒 Security Features

✅ **Password Hashing**
- Bcrypt with salt rounds
- Never stored in plaintext

✅ **JWT Tokens**
- HS256 encryption algorithm
- 30-day expiration
- Unique jti (JWT ID)

✅ **Input Validation**
- Email format verification
- Password length requirements (min 6 chars)
- SQL injection prevention via ORM

✅ **Error Handling**
- Generic error messages (no user enumeration)
- Account status checking
- Secure error responses

---

## 💻 Frontend Integration

### Login Modal
The frontend includes a built-in login/register modal that appears when users are not authenticated.

**Location:** `frontend/assets/js/auth.js`

**Features:**
- Tab-based login/register UI
- Client-side form validation
- Token storage in localStorage
- Automatic JWT header injection in all requests

### Usage in JavaScript

```javascript
// Get current token
const token = localStorage.getItem('auth_token');

// Check if authenticated
const isAuthenticated = AuthSystem.isAuthenticated();

// Login
AuthSystem.login('user@example.com', 'password123');

// Register
AuthSystem.register('user@example.com', 'password123', 'password123');

// Logout
AuthSystem.logout();
```

---

## 📦 Upgraded Dependencies

Added to `requirements.txt`:
```
Flask-SQLAlchemy==3.0.5
Flask-Bcrypt==1.0.1
Flask-JWT-Extended==4.5.2
```

---

## 🚀 Future Enhancements

### Planned Features
1. **Email Verification**
   - Verify email before account activation
   - Send confirmation links

2. **Password Reset**
   - Forgot password flow
   - Secure reset token

3. **Two-Factor Authentication**
   - TOTP (Time-based One-Time Password)
   - SMS verification

4. **Role-Based Access Control**
   - Admin, trader, viewer roles
   - Permission-based route access

5. **Subscription Management**
   - Plan upgrades/downgrades
   - Billing integration (Stripe)
   - Usage tracking per plan

6. **User Preferences**
   - Dashboard customization
   - Notification settings
   - API key management

---

## 🧪 Testing

### Test Registration
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Test Login
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Test Protected Route
```bash
curl -X GET http://localhost:5000/auth/me \
  -H "Authorization: Bearer <token>"
```

---

## ⚠️ Important Notes

1. **Change JWT Secret Key**
   - Update `JWT_SECRET_KEY` in `.env` in production
   - Never use default key in public deployments

2. **Database Location**
   - SQLite database: `backend/sofai_fx.db`
   - Backup database before updates

3. **Token Storage**
   - Tokens stored in browser localStorage
   - Consider using httpOnly cookies for production

4. **CORS Configuration**
   - Already enabled for `localhost:8080`
   - Update for your production domain

---

## 📊 User Model Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | Integer | Yes | Primary key |
| email | String(120) | Yes | Unique email |
| password | String(255) | Yes | Bcrypt hash |
| plan | String(20) | No | free/premium/enterprise |
| created_at | DateTime | Yes | Account creation |
| updated_at | DateTime | No | Last modification |
| is_active | Boolean | Yes | Account status |

---

## 🔄 Authentication Flow

```
1. User registers or logs in
   ↓
2. Credentials validated
   ↓
3. If valid:
   - Password hashed (register) / verified (login)
   - User stored in database (register)
   - JWT token generated
   ↓
4. Token returned to frontend
   ↓
5. Token stored in localStorage
   ↓
6. All API requests include token in Authorization header
   ↓
7. Backend validates token on each request
   ↓
8. Access granted if valid, 401 if expired/invalid
```

---

## 📝 Configuration

Add to `.env`:
```bash
JWT_SECRET_KEY=your-super-secret-key-change-in-production
```

Or use default: `sofai-fx-secret-key-change-in-production`

---

**Status:** ✅ **Production Ready** - Can be deployed with proper security hardening
