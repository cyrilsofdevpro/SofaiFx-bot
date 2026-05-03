# MongoDB Migration for Persistent Authentication

## Overview
This migration replaces SQLite with MongoDB Atlas for persistent user authentication that survives Render restarts.

## Changes Made

### 1. Dependencies Updated
- Added `pymongo==4.6.0`
- Added `motor==3.3.2`
- Added `mongoengine==0.27.0`

### 2. New Models Created (`models_mongo.py`)
- **User Model**: MongoDB version with all fields from SQLAlchemy
- **Signal Model**: For trading signals
- **Trade Model**: For trade records
- **ExecutionLog Model**: For execution tracking
- **APIKey Model**: For API key management

### 3. Authentication Updated (`auth.py`)
- Registration now uses `User.objects()` instead of `User.query`
- Login uses MongoDB queries
- Password hashing with bcrypt maintained
- JWT token generation unchanged

### 4. Admin API Updated (`admin.py`)
- All user queries converted to MongoDB
- Statistics calculations updated for MongoDB aggregation
- Admin authorization decorator updated

### 5. Flask App Updated (`flask_app.py`)
- Database initialization changed to `init_mongo_db()`
- Admin seeding moved to `seed_admin()` function
- Removed old SQLAlchemy bootstrap function

### 6. User Context Service Updated (`user_context.py`)
- API key lookups use MongoDB
- User object retrieval uses MongoDB

### 7. Configuration Updated (`config.py`)
- Added `MONGO_URI` environment variable

### 8. Environment Variables (`.env`)
- Added MongoDB connection string
- Admin credentials configured

## MongoDB Atlas Setup

### 1. Create MongoDB Atlas Account
1. Go to [mongodb.com/atlas](https://mongodb.com/atlas)
2. Create free account
3. Create new cluster (free tier)

### 2. Get Connection String
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy the connection string

### 3. Update Environment Variables
In Render dashboard, set:
```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/sofaifx
JWT_SECRET=your_jwt_secret_here
```

## Testing

### Local Testing
```bash
cd backend
python test_mongodb.py
```

### Deployed Testing
```bash
# Test login
curl -X POST https://your-render-url.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"cyriladmin@gmail.com","password":"Admin1234"}'
```

## Key Benefits

### ✅ Persistence
- Users survive Render restarts
- Admin accounts persist permanently
- No more "invalid login" after deployment

### ✅ Scalability
- MongoDB handles concurrent connections better
- Easy horizontal scaling
- Better performance for user operations

### ✅ Production Ready
- Cloud-hosted database
- Automatic backups
- High availability

## Migration Checklist

- [x] MongoDB dependencies installed
- [x] Models converted to MongoEngine
- [x] Auth endpoints updated
- [x] Admin API updated
- [x] User context service updated
- [x] Configuration updated
- [x] Environment variables set
- [x] Admin seeding implemented
- [x] Testing script created
- [ ] MongoDB Atlas cluster created
- [ ] Connection string configured in Render
- [ ] Deployed and tested

## Troubleshooting

### Connection Issues
- Verify MongoDB URI format
- Check network access from Render
- Ensure database user has correct permissions

### Authentication Issues
- Verify admin email/password in environment
- Check JWT secret consistency
- Test with local MongoDB first

### Performance Issues
- Add database indexes for frequently queried fields
- Monitor connection pool settings
- Consider read preferences for global deployment

## Rollback Plan

If issues occur, you can temporarily revert to SQLite by:
1. Commenting out MongoDB initialization
2. Uncommenting SQLAlchemy initialization
3. Using `models.py` instead of `models_mongo.py`

But note: existing users in MongoDB won't transfer to SQLite.