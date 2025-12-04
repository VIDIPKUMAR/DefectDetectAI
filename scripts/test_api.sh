#!/bin/bash
echo "🧪 Testing API endpoints..."

# Start API in background
python src/main.py &
API_PID=$!

# Wait for API to start
sleep 5

# Test endpoints
echo "1. Testing health endpoint..."
curl -s http://localhost:8000/health | python -m json.tool

echo -e "\n2. Testing ready endpoint..."
curl -s http://localhost:8000/ready | python -m json.tool

echo -e "\n3. Testing root endpoint..."
curl -s http://localhost:8000/ | python -m json.tool

# Kill API
kill $API_PID
echo -e "\n✅ API tests completed!"