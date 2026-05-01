# Hugging Face Spaces Deployment Guide

## Overview
This guide covers deploying SofAi-Fx to Hugging Face Spaces using Docker.

## Prerequisites
- [Hugging Face account](https://huggingface.co)
- Existing Space or ability to create one
- Git installed locally

## Deployment Steps

### 1. Create Hugging Face Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Fill in:
   - **Space name**: `sofaifx-bot` (or your preferred name)
   - **License**: MIT
   - **Space SDK**: **Docker** (NOT Gradio/FastAPI)
   - **Visibility**: Public or Private
4. Click **"Create Space"**

### 2. Clone Space Repository

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/sofaifx-bot
cd sofaifx-bot
```

### 3. Copy Project Files

Copy these into the cloned directory:
- Entire `backend/` folder (with all source code)
- `requirements.txt` (from root)
- `Dockerfile` (from root)
- `.env` (create with your API keys - see below)

```bash
cp -r /path/to/SofAi-Fx/backend .
cp /path/to/SofAi-Fx/requirements.txt .
cp /path/to/SofAi-Fx/Dockerfile .
cp /path/to/SofAi-Fx/backend/.env .env  # Copy your API keys
```

### 4. Create .env File

Create `backend/.env` in the Space repo with your credentials:

```bash
# Data APIs
ALPHA_VANTAGE_API_KEY=your_key_here
TWELVEDATA_API_KEY=your_key_here

# Hugging Face
HF_API_KEY=your_hf_token_here

# Optional: Telegram/Email for notifications
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SMTP_SERVER=smtp.gmail.com
SENDER_EMAIL=
SENDER_PASSWORD=

# Flask
FLASK_PORT=7860
JWT_SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=sqlite:///sofai_fx.db
```

### 5. Verify Files

Your Space directory should look like:
```
sofaifx-bot/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   ├── signals/
│   │   ├── backtesting/
│   │   └── main.py (entry point)
│   ├── .env (API keys)
│   └── requirements.txt
├── Dockerfile (builds on port 7860)
├── requirements.txt (root)
└── README.md (optional)
```

### 6. Commit and Push

```bash
git add -A
git commit -m "Deploy SofAi-Fx to Hugging Face Spaces

- Docker configuration for Python 3.11
- Flask app runs on port 7860
- All dependencies locked to stable versions
- Hugging Face API integration included"

git push
```

### 7. Monitor Build

1. Go to your Space: `huggingface.co/spaces/YOUR_USERNAME/sofaifx-bot`
2. Click **"Build logs"** in the top-right
3. Wait for build to complete (usually 5-10 minutes)
4. Once complete, your app will be live at the Space URL

## Accessing Your Deployment

Once live, your API endpoints are available at:
```
https://huggingface.co/spaces/YOUR_USERNAME/sofaifx-bot
```

### Example API Requests

**Health Check:**
```bash
curl https://huggingface.co/spaces/YOUR_USERNAME/sofaifx-bot/api/health
```

**Generate Signal (example EURUSD):**
```bash
curl -X POST https://huggingface.co/spaces/YOUR_USERNAME/sofaifx-bot/api/signals \
  -H "Content-Type: application/json" \
  -d '{"pair": "EURUSD"}'
```

## Troubleshooting

### Build fails with "Python version error"
- ✅ Check: Dockerfile uses `python:3.11-slim`
- ✅ Check: `requirements.txt` has stable versions

### "ModuleNotFoundError" during build
- ✅ Ensure `backend/src/main.py` exists
- ✅ Check: `sys.path` includes backend
- ✅ Verify: All dependencies in `requirements.txt`

### Port connection errors
- ✅ Dockerfile must `EXPOSE 7860`
- ✅ Flask must run on port 7860 (set via `FLASK_PORT=7860` env var)
- ✅ Never hardcode ports in code

### HF API integration not working
- ✅ Verify `HF_API_KEY` in `.env`
- ✅ Check: Key not expired or revoked
- ✅ Test locally: `.venv\Scripts\python.exe test_hf_integration.py`

### Slow builds / compilation errors
- ✅ Dockerfile uses `--upgrade pip setuptools wheel`
- ✅ `requirements.txt` has prebuilt wheels (not source)
- ✅ scikit-learn and pandas have binary builds available

## Performance Tips

1. **Cold starts**: First request takes 2-3 seconds (normal for Spaces)
2. **Rate limits**: HF applies rate limits to public Spaces
3. **Database**: SQLite works, but consider migrating to cloud DB for production
4. **Logging**: Logs visible in Space's "Runtime logs" section

## Security Notes

- ⚠️ Never commit `.env` file to git (add to `.gitignore`)
- ✅ Use Hugging Face Secrets for sensitive keys
- ✅ Enable JWT authentication for API endpoints
- ✅ Consider private Space if handling real trading data

## Updating Your Deployment

To update code:

```bash
# Pull latest from your repo
git pull

# Make changes
# ... edit files ...

# Commit and push
git add -A
git commit -m "Update: ..."
git push

# HF Spaces auto-rebuilds on push
```

## Next Steps

1. Test API endpoints locally before deploying
2. Set up monitoring/alerting for your deployment
3. Configure Telegram/Email notifications if needed
4. Add authentication tokens for secure API access
5. Consider using Hugging Face Secrets for production API keys

---

For more details on HF Spaces: https://huggingface.co/docs/hub/spaces
