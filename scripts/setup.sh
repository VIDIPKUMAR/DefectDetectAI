#!/bin/bash
echo "🚀 Setting up Kubernetes ML System..."

# Exit conda environment if active (CRITICAL FIX)
conda deactivate 2>/dev/null || true

# Remove old venv to start fresh
if [ -d "venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf venv
fi

# Use system Python (not Anaconda)
echo "Creating virtual environment with system Python..."
/usr/bin/python3 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install dependencies - USE LIGHT VERSION
echo "Installing dependencies..."

# First check if light requirements exist
if [ -f "requirements-light.txt" ]; then
    echo "Using light requirements (no compilation needed)..."
    pip install -r requirements-light.txt
else
    # Try with standard requirements, fallback to core packages
    echo "Trying standard requirements..."
    if ! pip install -r requirements.txt 2>/dev/null; then
        echo "Standard install failed, installing core packages only..."
        pip install fastapi uvicorn numpy opencv-python-headless pillow redis
    fi
fi

# Create necessary directories
mkdir -p data/upload models logs

# Verify installation
echo -e "\n✅ Verification:"
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import cv2; print('OpenCV:', cv2.__version__)"
python -c "import redis; print('Redis client available')"

echo -e "\n✅ Setup complete!"
echo "To run locally: python src/main.py"
echo "To test: ./scripts/test_api.sh"
echo -e "\nNote: Virtual environment is now active"
echo "To reactivate later: source venv/bin/activate"
