# Notes API

Учебный REST-сервис заметок. Python, Flask и PostgreSQL 16.

## Запуск

```bash
cp .env.example .env
# Задайте случайный DB_PASSWORD в .env.
docker compose up --build -d --wait
curl http://localhost:8000/health
```

| Запрос | Результат |
|---|---|
| GET /notes | Список заметок |
| POST /notes | Создание, JSON `{"text":"Заметка"}` |
| GET /notes/{id} | Одна заметка |
| PUT /notes/{id} | Замена текста, тот же формат JSON |
| DELETE /notes/{id} | Удаление |

Создание возвращает 201, чтение и изменение — 200, удаление — 204. Для неверного JSON, типа или длины текста возвращается 400 с полем `error`, для отсутствующего id — 404. Длина текста: 1–200 символов. Порт PostgreSQL наружу не опубликован; данные сохраняются в томе `db-data`.

Dockerfile содержит этап сборки колёс зависимостей и этап запуска приложения. Сервер работает от пользователя с UID 10015. `/metrics` отдаёт метрики Prometheus.

Коллекция проверок находится в `postman/notes.postman_collection.json`. Перед запуском задайте `baseUrl`, например `http://localhost:8000`.

```bash
postman collection run postman/notes.postman_collection.json --env-var baseUrl=http://localhost:8000
docker compose down
```

`docker compose down -v` удаляет и данные учебной БД.
