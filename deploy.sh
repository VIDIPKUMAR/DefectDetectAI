#!/bin/bash
echo "🚀 Deploying ML System to Kubernetes..."

# Build Docker image
echo "1. Building Docker image..."
docker build -t defect-detector:latest .

# For local Kubernetes (Minikube/Docker Desktop)
# Load image to local registry
if command -v minikube &> /dev/null; then
    minikube image load defect-detector:latest
elif [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Docker Desktop
    echo "Using Docker Desktop Kubernetes"
fi

# Apply Kubernetes manifests
echo "2. Deploying to Kubernetes..."
kubectl apply -f kubernetes/

# Wait for deployment
echo "3. Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=defect-detector --timeout=60s

# Get service URL
echo "4. Getting service URL..."
if command -v minikube &> /dev/null; then
    minikube service defect-detector-service --url
else
    kubectl get service defect-detector-service
fi

echo " Deployment complete!"
