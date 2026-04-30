# Multi-Account Session Management

## Overview

Each user now has a completely isolated personal account. When you attempt to log in as a different user on the same browser, the system detects this and gives you the option to switch accounts instead of automatically logging you in.

## Features

### 1. **Automatic User Switch Detection** 🔄
When you navigate to the dashboard with a different account:
- The system detects that you're trying to access as a different user
- A dialog box appears showing:
  - Your previously logged-in account email
  - The new account you're attempting to access
  - Your name for the new account

### 2. **Account Switch Dialog Options**
You can choose to:

**✅ Continue as [User Name]**
- Logs you into the new account
- Replaces the previous session
- Maintains the new user's data and settings

**🚪 Logout & Login Different**
- Logs you out completely
- Clears all session data
- Returns you to the login screen to log in properly

### 3. **Manual Account Switching** 
A new "Switch" button is available in the top navigation bar:
- Click the yellow **Switch** button (next to the Admin button)
- Confirms you want to switch accounts
- Logs you out and returns to login screen
- You can then log in with a different account

## How It Works

### Session Tracking
- Your account email is stored in `sessionStorage` (browser session only)
- When you refresh or navigate back, the system checks if you're the same user
- If different, a confirmation dialog appears

### Data Isolation
- Each user has completely separate:
  - API Keys
  - MT5 Credentials
  - Trading Signals
  - Account Settings
  - Performance Data
- Users cannot see or access other users' data

### Token Management
- Authentication tokens are stored in `localStorage` (persists across refreshes)
- Tokens are unique per user
- When you switch accounts, the old token is cleared and replaced

## Usage Scenarios

### Scenario 1: Sharing a Browser
**Person A** logs in as `alice@example.com`
1. Opens dashboard, sees their signals and account data
2. **Person B** wants to use the same browser
3. Copies the dashboard URL and opens it in the same browser
4. The system detects Person A was logged in
5. A dialog appears asking to confirm the account switch
6. Person B can:
   - Click "Continue" to log into their account (alice's data will be replaced)
   - Click "Logout & Login Different" to start fresh

### Scenario 2: Manual Account Switching
1. Click the **Switch** button in the top right
2. Confirm the account switch
3. You're logged out and returned to the login page
4. Log in with a different email address

### Scenario 3: Multiple Browsers/Tabs
- Each browser tab/window can have a different user logged in
- The session detection only applies within the same tab
- Opening the same URL in a new tab will detect your current session

## Security Features

✅ **No Cross-User Data Exposure**
- Users can only access their own data
- Backend enforces user isolation on all API endpoints
- Credentials are encrypted and stored per-user

✅ **Session Isolation**
- Each user session is completely separate
- Session data is not shared between users
- Clearing cache/cookies from one user doesn't affect others

✅ **Token Validation**
- All API requests require a valid token
- Tokens are tied to specific users
- Expired or invalid tokens automatically trigger re-authentication

## Troubleshooting

### Q: I'm not seeing the user switch dialog
**A:** 
- Clear your browser cache and cookies
- Refresh the page (Ctrl+F5 or Cmd+Shift+R)
- Make sure you're using the same browser tab

### Q: The "Switch" button isn't showing
**A:**
- Make sure you're logged in
- The button is in the top right navigation bar (yellow color)
- Try refreshing the page

### Q: I want to log in as a different user without the dialog
**A:**
- Click the **Switch** button and confirm
- Or manually click **Logout** and log in with different credentials

### Q: Can multiple users be logged in at the same time on the same device?
**A:**
- **Same browser tab**: No, only one user at a time
- **Different browser tabs**: Yes, each tab can have a different user
- **Different browsers**: Yes, each browser has its own session

## Data Persistence

### What stays when you switch accounts:
- Browser cache and cookies (general)
- Browser UI preferences (theme, layout)

### What gets cleared when you switch accounts:
- User authentication token
- Current user email (session tracking)
- User-specific data and settings
- API keys and credentials

## Best Practices

1. **Use the Switch button** for clean account switching
2. **Close the browser tab** if sharing a computer for security
3. **Log out when done** if using a shared device
4. **Use private/incognito browsing** for temporary access on shared devices
5. **Clear browser data** after shared access for maximum security

