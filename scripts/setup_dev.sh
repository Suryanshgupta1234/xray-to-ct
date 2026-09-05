#!/usr/bin/env bash
set -e

echo "========================================================"
echo " Setting up X-Ray to CT Translation Development Stack"
echo "========================================================"

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "Installing Python dependencies..."
python3 -m pip install -r backend/requirements.txt

echo "Installing Frontend packages..."
(cd frontend && npm install)

echo "Generating mock dataset..."
python3 datasets/sample_generator.py --train 24 --val 6 --test 6 --seed 42
python3 datasets/dataset_validator.py

echo ""
echo "[SUCCESS] Environment ready!"
