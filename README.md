# Star Distance Calculate Service

Асинхронный микросервис для вычисления расстояний до звёзд на основе параллакса.

## Описание

Сервис принимает данные о параллаксе звёзд, вычисляет расстояния в фоновом режиме и отправляет результаты обратно через callback URL.

**Формула расчёта**: `distance = 1000 / parallax` (в парсеках)

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd async-service/star_distance_calculate_service
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
SECRET_KEY=your-generated-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CALLBACK_URL=http://10.236.255.130:8080/callback-calculate-service
MAX_WORKERS=5
```

> **Важно**: Для генерации SECRET_KEY используйте:
> ```python
> from django.core.management.utils import get_random_secret_key
> print(get_random_secret_key())
> ```

### 5. Запуск сервера

```bash
python manage.py runserver 0.0.0.0:8000
```

## API

### POST /

Принимает запрос на вычисление расстояний до звёзд.

**Request:**
```json
{
  "request_id": "unique-request-id",
  "token": "async-token-for-callback",
  "stars": [
    {
      "star_id": 1,
      "parallax": 0.5
    },
    {
      "star_id": 2,
      "parallax": 1.2
    }
  ]
}
```

**Response (немедленный):**
```
HTTP/1.1 204 No Content
```

Пустой ответ с кодом 204 означает, что запрос принят и будет обработан асинхронно.

**Callback (через ~5 секунд):**

Сервис отправит PUT запрос на `CALLBACK_URL` с заголовком `X-Async-Token`:

```json
{
  "request_id": "unique-request-id",
  "stars": [
    {
      "star_id": 1,
      "distance": 2000.0
    },
    {
      "star_id": 2,
      "distance": 833.333
    }
  ]
}
```

## Архитектура

- **Django 5.1.3** - веб-фреймворк
- **ThreadPoolExecutor** - асинхронная обработка (5 воркеров)
- **Requests** - HTTP клиент для callback

### Процесс обработки

1. Клиент отправляет POST запрос с данными звёзд
2. Сервис немедленно возвращает **HTTP 204 No Content**
3. Фоновая задача вычисляет расстояния (задержка 5 сек)
4. Результаты отправляются на callback URL

## Структура проекта

```
star_distance_calculate_service/
├── .env                    # Переменные окружения (не в git)
├── .env.example           # Шаблон переменных окружения
├── .gitignore             # Игнорируемые файлы
├── requirements.txt       # Зависимости Python
├── README.md             # Документация
├── manage.py             # Django management script
├── venv/                 # Виртуальное окружение (не в git)
├── distance_calculator/  # Django приложение
│   ├── __init__.py
│   ├── apps.py
│   └── views.py         # Логика вычислений
└── star_distance_calculate_service/  # Django проект
    ├── __init__.py
    ├── settings.py      # Настройки Django
    ├── urls.py          # URL маршруты
    ├── asgi.py
    └── wsgi.py
```

## Разработка

### Очистка кэша Python

```bash
# Windows PowerShell
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force

# Linux/Mac
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Тестирование

Пример запроса с помощью curl:

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test-123",
    "token": "test-token",
    "stars": [
      {"star_id": 1, "parallax": 0.5},
      {"star_id": 2, "parallax": 2.0}
    ]
  }'
```

**Ожидаемый ответ:**
```
HTTP/1.1 204 No Content
```

## Безопасность

- ✅ SECRET_KEY в переменных окружения
- ✅ DEBUG отключён в production
- ✅ ALLOWED_HOSTS настроен
- ✅ CALLBACK_URL конфигурируется
- ⚠️ Нет аутентификации (добавьте при необходимости)

## Производительность

- **Max Workers**: 5 (настраивается через `MAX_WORKERS`)
- **Задержка обработки**: 5 секунд (имитация вычислений)
- **Timeout запросов**: 10 секунд

## Troubleshooting

### Ошибка "Insufficient permissions"
Проверьте, что callback URL доступен и принимает PUT запросы с заголовком `X-Async-Token`.

### Callback не приходит
- Проверьте логи сервиса
- Убедитесь, что `CALLBACK_URL` правильный
- Проверьте сетевую доступность

## Лицензия

MIT
