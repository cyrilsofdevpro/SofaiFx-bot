# 🎛️ SofAi FX Admin Dashboard - Setup & Usage Guide

## 📋 Overview

The Admin Dashboard is a powerful control center for managing your SofAi FX trading bot system. It provides complete visibility and control over users, signals, and system health.

---

## 🚀 Quick Start

### 1. **Set First User as Admin**

Run this command in your backend directory:

```bash
cd backend
python setup_admin.py
```

This makes the first registered user an admin with full access to the admin dashboard.

### 2. **Access Admin Dashboard**

Once you're logged in to the main dashboard, you'll see a **👑 Admin** button (purple) in the navigation bar (visible only to admin users).

Click it or navigate directly to: **`http://localhost:8080/admin.html`**

---

## 🎯 Main Features

### **1. Overview (Main Page)**
Your system control center with key metrics:
- **Total Users** - All registered users
- **Active Users (24h)** - Users active in last 24 hours
- **Signals Today** - Signals generated today
- **Average Confidence** - Avg confidence of today's signals
- **Signal Distribution** - Buy vs Sell pie chart
- **API Status** - Real-time API health (TwelveData, Alpha Vantage, Telegram, Email)
- **System Information** - Database & Scheduler status

### **2. User Management**
Complete user administration:
- **View all users** with pagination
- **User info**: Name, Email, Plan, Status, Signal count, Last active time
- **User actions**:
  - 🚫 **Disable/Enable** - Turn user accounts on/off
  - 👑 **Make/Revoke Admin** - Grant admin privileges
  - 📊 **View Signals** - See user's trading signals
  - 💳 **Change Plan** - Switch between free/premium/enterprise

### **3. Signals Analytics**
Deep insight into trading signals:
- **Total Signals** - All time signal count
- **Buy/Sell Ratio** - Ratio of buy to sell signals
- **Signal Timeline (30 days)** - Line chart showing signal volume over time
- **Top Pairs** - Most analyzed currency pairs with confidence metrics
- **Signal breakdown** - Buy, Sell, Hold counts
- **Confidence distribution** - By signal type

### **4. System Monitoring**
Track system health:
- **Database Size** - SQLite DB file size in MB
- **Total Users** - User count from database
- **Total Signals** - Total signals stored
- **Recent Logs** - Latest log files and their sizes
- **System Status** - Database connection, Scheduler state
- **Error tracking** - Recent error logs

### **5. Notifications Control**
Manage user communications:
- **Test Notifications** - Send test alerts via Telegram, Email, or both
- **Broadcast Messages** - Send announcements to all active users
- **Custom titles & messages** - Personalized communications

---

## 🔐 Security & Access Control

### **Admin-Only Protection**
- All admin routes require valid JWT token + admin role
- Non-admin users get 403 Forbidden response
- Admin status verified on every request
- Last active time tracked for auditing

### **How It Works**
1. User logs in with JWT token
2. Admin middleware checks `is_admin` flag in database
3. If `is_admin = False`: Access denied (403)
4. If `is_admin = True`: Access granted, `last_active` updated
5. All actions are logged

---

## 📊 Dashboard Tabs Explained

### **Overview Tab**
- Default landing page
- Shows system-wide statistics
- Real-time API status
- Quick health check

### **Users Tab**
**Table shows:**
| Column | Info |
|--------|------|
| Name | User name (with ADMIN badge if applicable) |
| Email | User email address |
| Plan | free/premium/enterprise |
| Status | Active/Inactive |
| Signals | Total signals generated |
| Actions | Disable/Admin/View buttons |

**Pagination:** 20 users per page, navigable with buttons

### **Signals Tab**
- Total all-time signals
- Buy/Sell ratio metric
- 30-day signal timeline graph
- Top 20 pairs by volume
- Confidence averages per pair

### **System Tab**
- Database file size (in MB and bytes)
- User and signal counts from database
- Recent log files list
- System status indicators
- Uptime information

### **Notifications Tab**
- **Test Channel** selector (Telegram/Email/All)
- **Send Test** button - Verify notifications work
- **Broadcast Title** input
- **Broadcast Message** textarea
- **Send Broadcast** - Message all active users

---

## 🎨 UI Features

### **Real-time Updates**
- Auto-refresh every 30 seconds
- Manual refresh button in top right
- Last update timestamp displayed

### **Charts**
- **Signal Distribution** - Doughnut chart (Buy/Sell)
- **Signal Timeline** - Line graph (30-day history)
- **Top Pairs** - Vertical list with confidence bars

### **Status Badges**
- 🟢 **Active** - Green badge for enabled users/APIs
- 🔴 **Inactive** - Red badge for disabled users
- 🟣 **Admin** - Purple badge for admin users
- 🔵 **Plan types** - Color-coded plan badges

### **Action Buttons**
- **Disable/Enable** - Yellow text on dark background
- **Admin controls** - Purple text
- **View Details** - Blue text
- **Send notifications** - Blue/Purple action buttons

---

## 📈 Real-World Use Cases

### **Monitor System Health**
```
Check Overview tab → See if all APIs operational → Check database size
```

### **Manage New Users**
```
Users tab → Find new user → Toggle active if suspicious → Change plan if needed
```

### **Debug Signal Issues**
```
Signals tab → Check Buy/Sell ratio → View top pairs → Compare confidence trends
```

### **Send Announcements**
```
Notifications tab → Write message → Click Send Broadcast → All users get email
```

### **Troubleshoot Problems**
```
System tab → Check DB size/connection → View recent logs → Identify errors
```

---

## 🔧 API Endpoints (For Developers)

All endpoints protected with JWT + admin check:

```
GET    /admin/stats/overview           → Main statistics
GET    /admin/users                    → List all users (paginated)
POST   /admin/users/<id>/toggle-active → Disable/enable user
POST   /admin/users/<id>/toggle-admin  → Grant/revoke admin
POST   /admin/users/<id>/change-plan   → Update subscription plan
GET    /admin/users/<id>/signals       → Get user's signals
GET    /admin/signals/analytics        → Signal analytics & trends
GET    /admin/system/status            → System health info
POST   /admin/notifications/test       → Send test notification
POST   /admin/notifications/broadcast  → Send broadcast to all
GET    /admin/current-admin            → Current admin info
```

---

## 🐛 Troubleshooting

### **Can't see Admin button?**
- Not logged in? Log in first
- Not admin? Run `python setup_admin.py` to promote first user
- Wrong URL? Should be `/admin.html` (not `/admin/`)

### **Admin Dashboard shows "Error loading users"?**
- Backend Flask not running? Start it: `python -m src.api.flask_app`
- Database corrupted? Backup and recreate
- Network issue? Check `localhost:5000/health`

### **Test notification not sending?**
- Telegram not configured? Check `.env` file for `TELEGRAM_BOT_TOKEN`
- Email not working? Verify Gmail app password in `.env`
- API rate limited? Wait 1 minute and try again

### **Charts not showing?**
- JavaScript error? Check browser console (F12)
- Chart.js not loaded? Page should load CDN, check network tab
- No data? Might need to generate more signals first

---

## 💡 Tips & Best Practices

1. **Regular Monitoring** - Check Overview tab daily for health
2. **User Audit** - Review Users tab weekly for suspicious activity
3. **Signal Analysis** - Use Signals tab to identify winning pairs
4. **Test Before Broadcast** - Always send test notification first
5. **Backup Database** - Before making bulk user changes
6. **Monitor Logs** - Check System tab for errors
7. **Track Changes** - Use last_active timestamp to audit admin actions

---

## 📝 Making Your First Admin User

When you first run `setup_admin.py`, it:
1. Finds the earliest registered user (usually your first user)
2. Sets `is_admin = True` in the database
3. Returns the user's name and email
4. Confirms the admin dashboard URL

```
Example output:
✅ User 'Cyril Sofdev' (cyril@sofai.com) is now an ADMIN
   You can now access: http://localhost:8080/admin.html
```

---

## 🎓 Next Steps

1. ✅ Set first user as admin
2. ✅ Log in and access admin dashboard
3. ✅ Explore each tab
4. ✅ Review current users and signals
5. ✅ Send a test notification
6. ✅ Monitor signals for patterns
7. ✅ Broadcast a message to users
8. ✅ Track system metrics over time

---

**🚀 Your SofAi FX Bot is now fully managed!**

Questions? Check logs or enable debug mode for more details.
