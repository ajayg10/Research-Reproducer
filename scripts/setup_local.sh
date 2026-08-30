#!/bin/bash

# Local setup script for development

echo "=== Autonomous Research Reproducibility Engine - Setup ==="

# Check prerequisites
echo ""
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi
echo "✓ Python found: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi
echo "✓ Node.js found: $(node --version)"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker"
    exit 1
fi
echo "✓ Docker found: $(docker --version)"

# Setup backend
echo ""
echo "Setting up backend..."
cd backend || exit

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

cd ..

# Setup frontend
echo ""
echo "Setting up frontend..."
cd frontend || exit

echo "Installing Node.js dependencies..."
npm install --silent

cd ..

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GEMINI_API_KEY"
fi

# Pull Docker image
echo ""
echo "Pulling Docker base image for sandbox..."
docker pull python:3.11-slim

# Create directories
echo ""
echo "Creating directories..."
mkdir -p storage/pipelines storage/artifacts storage/uploads
mkdir -p generated sandbox

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GEMINI_API_KEY"
echo "2. Start backend: cd backend && source venv/bin/activate && python main.py"
echo "3. Start frontend: cd frontend && npm run dev"
echo "4. Open http://localhost:5173"
echo ""
