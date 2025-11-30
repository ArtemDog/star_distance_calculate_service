# app/views.py
import json
import time
import os
import logging
import requests
from concurrent.futures import ThreadPoolExecutor

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Configure logging
logger = logging.getLogger(__name__)

# Load configuration from environment variables
CALLBACK_URL = os.getenv('CALLBACK_URL', 'http://192.168.1.21:8080//update-calculated-distance')
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '5'))

executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)


def calculate_distance(stars):
    """Вычисление расстояний: distance = 1000 / parallax"""
    result = []
    for star in stars:
        try:
            parallax = star.get("parallax", 0)
            if parallax == 0:
                logger.warning(f"Star {star.get('star_id')} has zero parallax, skipping")
                continue
            distance = 1000 / parallax
            result.append({
                "star_id": star["star_id"],
                "distance": round(distance, 3)
            })
        except (KeyError, TypeError, ZeroDivisionError) as e:
            logger.error(f"Error calculating distance for star {star.get('star_id')}: {e}")
    return result


def background_task(request_id, token, stars):
    """Задача, выполняющаяся в фоне — считает расстояния и шлёт результат назад"""
    
    time.sleep(5)
    
    distances = calculate_distance(stars)
    
    payload = {
        "request_id": int(request_id),
        "stars": distances
    }
    
    headers = {
        "X-Async-Token": token,
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.put(CALLBACK_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"[OK] Callback sent to main service: request_id={request_id}, stars_count={len(distances)}")
    except requests.exceptions.Timeout:
        logger.error(f"[ERROR] Callback timeout for request_id={request_id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"[ERROR] Callback failed for request_id={request_id}: {e}")


@csrf_exempt
def set_status(request):
    """Приём JSON от главного сервера"""
    if request.method != "POST":
        return JsonResponse({"error": "Use POST"}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        request_id = data.get("request_id")
        token = data.get("token")
        stars = data.get("stars", [])
        
        if not request_id or not token:
            return JsonResponse({"error": "Missing required fields: request_id, token"}, status=400)
        
        if not isinstance(stars, list):
            return JsonResponse({"error": "stars must be a list"}, status=400)
        
        logger.info(f"Received request: request_id={request_id}, stars_count={len(stars)}")
        
        # Запускаем фоновую задачу
        executor.submit(background_task, request_id, token, stars)
        
        # Мгновенный ответ главному серверу - 204 No Content
        return HttpResponse(status=204)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON received")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
