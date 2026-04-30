# MetaTrader5 (MT5) Setup Guide

## ⚠️ Important: MT5 Terminal Required

The SofAi FX bot requires the **MetaTrader5 terminal application** to be running on your Windows computer. The Python library we use is only a wrapper that communicates with the MT5 terminal.

## Prerequisites

### 1. Download MetaTrader5 Terminal
- Visit your broker's website (e.g., JustMarkets, ICMarkets, Exness, etc.)
- Download the MetaTrader5 terminal application for your broker
- **Example**: For JustMarkets → Download from https://www.justmarkets.com/

### 2. Install and Launch MT5 Terminal
1. Run the MT5 installer
2. Complete the installation
3. Launch the MT5 terminal application
4. Log in with your trading account credentials
5. **Keep the MT5 terminal open** while using SofAi FX bot

### 3. Verify Your Credentials
Before connecting through SofAi FX, verify that you can:
- Log into the MT5 terminal directly with your credentials
- See your account balance and open positions
- The terminal should display your account number

## Connecting Through SofAi FX

### Step 1: Open MT5 Connection
1. Go to "MT5 Account" tab in the dashboard
2. Enter your MT5 credentials:
   - **Login ID**: Your MT5 account number (e.g., 2002073009)
   - **Password**: Your MT5 password
   - **Server**: Select your broker's server from the dropdown

### Step 2: Connect
- Click the "Connect" button
- Wait a few seconds for the connection to establish
- The MT5 terminal should already be running on your computer

### Step 3: Verify Connection
- You should see a "Connected" status
- Your account balance will be displayed
- Your open positions will appear

## Troubleshooting

### Error: "MT5 terminal is not running"
**Solution**: 
- Start the MetaTrader5 terminal application on your computer
- Ensure it stays open while using the bot
- The terminal icon should appear in your system tray

### Error: "Authorization failed"
**Possible causes**:
1. Wrong login credentials - verify in the MT5 terminal first
2. Wrong server name - check the exact server name in MT5 terminal settings
3. Account not available for API - some brokers require enabling API access

**Solution**:
- Test your credentials directly in the MT5 terminal first
- Double-check the server name (it's case-sensitive)
- Contact your broker if the account is restricted

### Error: "Server not found"
**Solution**:
- Verify the server name is spelled correctly
- Check the MT5 terminal for the exact server name
- Use the dropdown in the connection form (don't type manually)

## Common Server Names

- `JustMarkets-Demo` (JustMarkets Demo)
- `JustMarkets-Real` (JustMarkets Live)
- `ICMarkets-Demo` (IC Markets Demo)
- `ICMarkets-Real` (IC Markets Live)
- `Exness-Demo` (Exness Demo)
- `Exness-Real` (Exness Live)

Check your MT5 terminal to confirm the exact server name for your account.

## Multi-Account Setup

You can connect different MT5 accounts by:
1. Disconnecting the current account
2. Changing the credentials
3. Clicking Connect for the new account

Only one account can be connected at a time.

## Security Notes

- Your MT5 credentials are encrypted and stored securely in the database
- They are never transmitted in plain text
- Each user has isolated credentials stored separately
- The bot only uses credentials for executing trades you've authorized

## Still Having Issues?

1. Check that MT5 terminal is running and logged in
2. Verify credentials work directly in MT5 terminal
3. Check the browser console (F12) for detailed error messages
4. Check the backend logs for more information
5. Contact your broker's support team

