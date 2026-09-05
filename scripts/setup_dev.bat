@echo off
echo ========================================================
echo  Setting up X-Ray to CT Translation Development Stack
echo ========================================================

REM 1. Generate local environment file if missing
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

REM 2. Install backend dependencies
echo Installing Python dependencies...
python -m pip install -r backend\requirements.txt

REM 3. Install frontend dependencies
echo Installing Frontend packages...
cd frontend
call npm install
cd ..

REM 4. Generate mock dataset
echo Generating mock dataset...
python datasets\sample_generator.py --train 24 --val 6 --test 6 --seed 42
python datasets\dataset_validator.py

echo.
echo [SUCCESS] Environment ready! Run scripts\run_local.bat to start.
