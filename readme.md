# Офис

Домашнее задание 7 «Деплой и инфраструктура».

Проект на Django для учета сотрудников и рабочих мест: сайт с каталогом сотрудников и REST API на Django REST Framework.

## Что сделано в этом задании

- документация API в формате Swagger (drf-spectacular): `/api/docs/`, схема OpenAPI: `/api/schema/`;
- настроен CORS для открытого API (django-cors-headers): запросы к `/api/...` разрешены с любых сайтов;
- приложение обернуто в Docker, база данных PostgreSQL запускается через docker-compose;
- настройки (секретный ключ, режим отладки, база данных) берутся из переменных окружения.

## Запуск через Docker

Нужны установленные Docker и Docker Compose.

1. Перейти в папку проекта:

   ```bash
   cd dz_7
   ```

2. Собрать и запустить контейнеры:

   ```bash
   docker compose up --build
   ```

   Запустятся два контейнера: `db` (PostgreSQL) и `web` (Django). Контейнер `web` ждет, пока база будет готова, затем применяет миграции, создает группы «Смотритель» и «Администратор» и запускает сервер.

3. В другом терминале создать суперпользователя для входа в админку:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

4. Открыть в браузере:

   - сайт: http://localhost:8000/
   - документация API: http://localhost:8000/api/docs/
   - админка: http://localhost:8000/admin/

Остановить проект: `Ctrl+C` или `docker compose down`. Чтобы удалить и данные базы: `docker compose down -v`.

## Запуск без Docker

Без переменных `POSTGRES_*` проект работает с SQLite.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py create_roles
python manage.py createsuperuser
python manage.py runserver
```

Тесты: `python manage.py test`.

## Пользователи и права

- Посетитель (любой пользователь, в том числе без входа) может смотреть каталог сотрудников. Подробная карточка доступна после входа.
- Смотритель (группа «Смотритель») может перемещать сотрудников между столами.
- Администратор (группа «Администратор») может добавлять, изменять и удалять сотрудников и перемещать их между столами.

Группу пользователю назначает суперпользователь в админке.

## Адреса API

| Метод | Адрес | Что делает | Кто может |
|---|---|---|---|
| POST | `/api/token/` | получить JWT по логину и паролю | все |
| POST | `/api/token/refresh/` | обновить access токен | все |
| GET | `/api/employees/` | список сотрудников по 10 на странице | все |
| GET | `/api/employees/{id}/` | подробная карточка сотрудника | вошедшие |
| POST | `/api/employees/` | добавить сотрудника | администратор |
| PUT, PATCH | `/api/employees/{id}/` | изменить сотрудника | администратор |
| DELETE | `/api/employees/{id}/` | удалить сотрудника | администратор |
| POST | `/api/employees/{id}/move/` | пересадить сотрудника за другой стол | смотритель, администратор |
| GET | `/api/skills/` | список навыков | все |
| GET | `/api/workplaces/` | список столов | вошедшие |

Фильтры списка сотрудников:

- `skill` - название навыка, например `?skill=Бэкенд`;
- `skills` - id навыков, сотрудник должен владеть всеми: `?skills=1&skills=2`;
- `min_experience`, `max_experience` - стаж в днях: `?min_experience=365`;
- `gender` - пол: `male` или `female`.

## Примеры

Получить токен:

```bash
curl -X POST http://localhost:8000/api/token/ -H 'Content-Type: application/json' -d '{"username": "admin", "password": "пароль"}'
```

Добавить сотрудника (нужен токен администратора):

```bash
curl -X POST http://localhost:8000/api/employees/ -H 'Authorization: Bearer <access>' -H 'Content-Type: application/json' -d '{"username": "ivanov", "first_name": "Иван", "last_name": "Иванов", "gender": "male", "skills": [{"skill": 1, "level": 7}]}'
```

Пересадить сотрудника за стол №3:

```bash
curl -X POST http://localhost:8000/api/employees/1/move/ -H 'Authorization: Bearer <access>' -H 'Content-Type: application/json' -d '{"desk_number": 3}'
```
