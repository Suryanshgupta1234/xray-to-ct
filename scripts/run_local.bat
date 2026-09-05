@echo off
echo ========================================================
echo  Launching X-Ray to CT Translation Platform
echo ========================================================
echo.
echo Starting FastAPI Backend on http://localhost:8000 ...
start "Backend (FastAPI)" cmd /k "python -m uvicorn app.main:app --app-dir backend --reload --port 8000"

echo Starting React/Vite Frontend on http://localhost:5173 ...
start "Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo  Services launched in separate windows!
echo  - Frontend UI:  http://localhost:5173
echo  - Swagger Docs: http://localhost:8000/api/v1/docs
echo  - Health Check: http://localhost:8000/api/v1/health
echo ========================================================
pause
