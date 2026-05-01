# Render Build Configuration

This file documents the required Render settings for deployment.

## Environment Setup

### Root Directory
Set to: `backend`

Render will use `/backend` as the project root for deployment.

### Build Command
```bash
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

This ensures:
- pip, setuptools, wheel are current (fixes scikit-learn compilation)
- All dependencies from backend/requirements.txt are installed

### Start Command
```bash
gunicorn src.main:app
```

## Configuration Files
- **runtime.txt**: Python 3.11.9 specification
- **requirements.txt**: All dependencies (updated for Python 3.11 compatibility)
- **Procfile**: Process configuration for Render

## Key Changes for Python 3.11 Stability
- numpy>=2.0.0 (was 1.24.3)
- pandas>=2.2.0 (was 2.0.3)
- setuptools>=65.0.0 (new)
- wheel>=0.40.0 (new)
- Python 3.11.9 (forced via runtime.txt)

## Expected Result
✅ Clean build without Cython errors
✅ All dependencies compile successfully
✅ Flask app starts on port 5000
✅ HF sentiment analysis functional
✅ APScheduler background jobs enabled
