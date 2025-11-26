# app/views.py
import json
import time
import random
import requests
from concurrent.futures import ThreadPoolExecutor

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

executor = ThreadPoolExecutor(max_workers=5)

CALLBACK_URL = "http://10.236.255.130:8080/callback-calculate-service"


def calculate_distance(stars):
    """Вычисление расстояний: distance = 1000 / parallax"""
    result = []
    for star in stars:
        distance = 1000 / star["parallax"]
        result.append({
            "star_id": star["star_id"],
            "distance": round(distance, 3)
        })
    return result


def background_task(request_id, token, stars):
    """Задача, выполняющаяся в фоне — считает расстояния и шлёт результат назад"""

    time.sleep(5)

    distances = calculate_distance(stars)


    payload = {
        "request_id": request_id,
        "stars": distances
    }

    headers = {
        "X-Async-Token": token,
        "Content-Type": "application/json",
    }

    try:
        requests.put(CALLBACK_URL, headers=headers, json=payload)
        print(f"[OK] Callback sent to main service: {payload}")
    except Exception as e:
        print(f"[ERROR] Callback failed: {e}")


@csrf_exempt
def set_status(request):
    """Приём JSON от главного сервера"""
    if request.method != "POST":
        return JsonResponse({"error": "Use POST"}, status=405)

    data = json.loads(request.body)

    request_id = data["request_id"]
    token = data["token"]
    stars = data["stars"]

    # Запускаем фоновую задачу
    executor.submit(background_task, request_id, token, stars)

    # Мгновенный ответ главному серверу
    return JsonResponse({"status": "accepted"})
