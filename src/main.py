"""
Kubernetes-native ML Application
"""
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
import cv2
import numpy as np
import asyncio
import redis
import json
import logging
from typing import Dict, Any
import io
from PIL import Image
import time

# Configure logging for Kubernetes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="K8s Defect Detection API")

# Redis client for caching (Kubernetes service discovery)
redis_client = None

def get_redis():
    """Get Redis connection with retry logic for Kubernetes"""
    global redis_client
    if redis_client is None:
        max_retries = 5
        for i in range(max_retries):
            try:
                # Kubernetes service name
                redis_client = redis.Redis(
                    host='redis-service',
                    port=6379,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                redis_client.ping()
                logger.info("✅ Connected to Redis")
                return redis_client
            except Exception as e:
                logger.warning(f"Redis connection attempt {i+1}/{max_retries} failed: {e}")
                time.sleep(2)
        raise Exception("Cannot connect to Redis")
    return redis_client

class DefectDetector:
    """ML Model for defect detection"""
    
    def __init__(self):
        self.model_loaded = False
        self.load_model()
    
    def load_model(self):
        """Load ML model (simplified for demo)"""
        # In production, this would load a trained model
        logger.info("Loading defect detection model...")
        time.sleep(1)  # Simulate model loading
        self.model_loaded = True
        logger.info("✅ Model loaded")
    
    async def detect_async(self, image_bytes: bytes) -> Dict[str, Any]:
        """Async defect detection"""
        try:
            # Convert bytes to image
            image = Image.open(io.BytesIO(image_bytes))
            image_np = np.array(image)
            
            if len(image_np.shape) == 2:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
            
            # Simple edge-based detection (replace with actual ML model)
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 10, 50)
            
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            defects = []
            total_defect_area = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 5000:
                    x, y, w, h = cv2.boundingRect(contour)
                    defects.append({
                        "bbox": [x, y, w, h],
                        "area": float(area),
                        "confidence": 0.85
                    })
                    total_defect_area += area
            
            # Calculate defect percentage
            total_area = image_np.shape[0] * image_np.shape[1]
            defect_percentage = (total_defect_area / total_area) * 100 if total_area > 0 else 0
            
            return {
                "defects_found": len(defects),
                "defect_percentage": round(defect_percentage, 2),
                "defects": defects,
                "status": "success",
                "processing_time_ms": 150  # Simulate processing time
            }
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return {
                "defects_found": 0,
                "error": str(e),
                "status": "error"
            }

detector = DefectDetector()

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Defect Detection API starting up...")
    # Test Redis connection
    try:
        get_redis()
    except Exception as e:
        logger.warning(f"Redis not available: {e}")

@app.get("/")
async def root():
    """Root endpoint with Kubernetes metadata"""
    return {
        "service": "defect-detector",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/ready",
            "/detect",
            "/metrics",
            "/batch-detect"
        ],
        "kubernetes_ready": True
    }

@app.get("/health")
async def health_check():
    """Kubernetes liveness probe"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "model_loaded": detector.model_loaded
    }

@app.get("/ready")
async def ready_check():
    """Kubernetes readiness probe"""
    try:
        # Check Redis connection
        redis_conn = get_redis()
        redis_conn.ping()
        return {
            "status": "ready",
            "redis": "connected",
            "model": "loaded" if detector.model_loaded else "loading"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )

@app.post("/detect")
async def detect_defect(file: UploadFile = File(...)):
    """Single image defect detection"""
    start_time = time.time()
    
    # Read image
    image_bytes = await file.read()
    
    # Generate cache key
    cache_key = f"detect:{hash(image_bytes)}"
    
    # Try cache first
    try:
        redis_conn = get_redis()
        cached_result = redis_conn.get(cache_key)
        if cached_result:
            result = json.loads(cached_result)
            result["cached"] = True
            result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
            logger.info(f"Cache hit for {cache_key}")
            return result
    except:
        pass  # Cache is optional
    
    # Process image
    result = await detector.detect_async(image_bytes)
    result["cached"] = False
    result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Cache result (TTL: 5 minutes)
    try:
        redis_conn = get_redis()
        redis_conn.setex(cache_key, 300, json.dumps(result))
    except:
        pass  # Cache is optional
    
    return result

@app.post("/batch-detect")
async def batch_detect(files: list[UploadFile] = File(...)):
    """Batch processing for multiple images"""
    tasks = []
    results = []
    
    for file in files:
        image_bytes = await file.read()
        task = detector.detect_async(image_bytes)
        tasks.append(task)
    
    # Process in parallel
    results = await asyncio.gather(*tasks)
    
    summary = {
        "total_images": len(results),
        "total_defects": sum(r.get("defects_found", 0) for r in results),
        "images_with_defects": sum(1 for r in results if r.get("defects_found", 0) > 0),
        "results": results
    }
    
    return summary

@app.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics for monitoring"""
    try:
        redis_conn = get_redis()
        # Get some Redis metrics
        redis_info = redis_conn.info()
        
        return {
            "defect_detector_requests_total": 1000,  # In real app, track this
            "defect_detector_requests_in_progress": 0,
            "defect_detector_model_load_status": 1 if detector.model_loaded else 0,
            "redis_connected_clients": redis_info.get('connected_clients', 0),
            "redis_used_memory": redis_info.get('used_memory', 0),
            "timestamp": time.time()
        }
    except Exception as e:
        return {"error": f"Metrics unavailable: {e}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)