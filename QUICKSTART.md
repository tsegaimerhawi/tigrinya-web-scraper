# Quick Start Guide

## Starting the Application

You need to run **two servers** - one for the backend (FastAPI) and one for the frontend (React).

### Option 1: Using the startup scripts (Easiest)

**Terminal 1 - Backend:**
```bash
./start-backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start-frontend.sh
```

### Option 2: Manual startup

**Terminal 1 - Backend:**
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment (if not exists)
python3 -m venv ../.env
source ../.env/bin/activate  # On Windows: ..\.env\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt
playwright install chromium

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
# Navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

## Access the Application

- **Frontend (Web UI):** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## Troubleshooting

### "Site cannot be reached" or Connection Refused

1. **Check if backend is running:**
   - Open http://localhost:8000/docs
   - If it doesn't load, the backend isn't running
   - Check Terminal 1 for errors

2. **Check if frontend is running:**
   - Open http://localhost:5173
   - If it doesn't load, the frontend isn't running
   - Check Terminal 2 for errors

3. **Check for port conflicts:**
   - Make sure ports 8000 and 5173 are not in use
   - You can change ports in the startup commands

4. **Install dependencies:**
   - Backend: `pip install -r backend/requirements.txt`
   - Frontend: `cd frontend && npm install`

5. **Check Python/Node versions:**
   - Python: `python3 --version` (should be 3.8+)
   - Node: `node --version` (should be 18+)

### Common Errors

**ModuleNotFoundError:**
- Make sure virtual environment is activated
- Run `pip install -r backend/requirements.txt`

**npm ERR:**
- Run `cd frontend && npm install`

**Playwright browser not found:**
- Run `playwright install chromium`
