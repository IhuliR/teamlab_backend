# TeamLab

TeamLab — платформа для формирования команд под pet-, учебные и некоммерческие проекты. Владелец создаёт проект и ищет участников на конкретные роли, а участник находит подходящие проекты и откликается на них.

## Проект и текущий статус

TeamLab развивается как командный продуктовый проект. Backend и frontend находятся в отдельных репозиториях:

* **Backend (этот репозиторий)** — Django/DRF API, доменная модель, аутентификация, permissions и основная бизнес-логика.
* **Frontend** — [TeamLab-Frontend](https://github.com/distinkt-dd/TeamLab-Frontend), разрабатывается отдельной frontend-командой на React и TypeScript.

Основной backend-функционал уже реализован. Текущий этап проекта — frontend-разработка и интеграция с готовым API, поэтому основная ежедневная активность сейчас находится во frontend-репозитории и его development-ветках. Backend продолжает обновляться по мере интеграции, уточнения API-контракта и исправления ошибок.

Команда проекта: Team Lead / Backend Developer, 3 frontend-разработчика и 1 дизайнер.

## Возможности

- регистрация пользователей и JWT-аутентификация;
- публичные каталоги проектов и участников с поиском и фильтрацией;
- профили пользователей, навыки, специализации, портфолио и избранные проекты;
- создание проектов вместе с ролями и требованиями к навыкам;
- заявки участников и приглашения владельцев с принятием или отклонением;
- учёт участия в команде, выход участника и исключение владельцем;
- системные справочники областей, специализаций и навыков;
- read-only уведомления о заявках и приглашениях, ожидающих решения.

## Backend: ключевые решения

- Основной workflow разделён на четыре сущности: `Project → ProjectRole → RoleInterest → ProjectMembership`.
- Applications и invitations используют одну модель `RoleInterest`; направление взаимодействия задаёт `source`, а жизненный цикл — `status`.
- Принятие `RoleInterest` и создание связанного `ProjectMembership` выполняются в одной транзакции. Напрямую создать membership через публичный API нельзя.
- Backend подбирает роль проекта по специализации участника. В одном проекте одна специализация представлена не более чем одной ролью, при этом на роли может быть несколько участников.
- Права зависят от сценария: owner управляет только своими проектами и обрабатывает входящие заявки, а приглашение принимает или отклоняет приглашённый participant.
- Каталоги проектов и пользователей поддерживают поиск и фильтрацию по областям, специализациям и навыкам; связанные выборки защищены от дубликатов.
- Ответы project detail и публичного профиля содержат вычисляемый пользовательский контекст: подходящую роль, текущую заявку или приглашение, membership и доступность контактов.
- JWT настроен с rotation refresh-токенов и blacklist; demo seed и API-тесты покрывают основные пользовательские и доменные сценарии.

## Стек

- **Backend:** Python, Django 5.1, Django REST Framework, Simple JWT, django-filter, django-cors-headers.
- **Database:** SQLite в текущей конфигурации; переход на PostgreSQL планируется перед deployment.
- **Testing:** pytest, pytest-django.
- **API contract:** OpenAPI 3.0, Postman collection.

Версии зависимостей зафиксированы в [`teamlab_backend/requirements.txt`](teamlab_backend/requirements.txt).

## Доменная модель

```text
Project → ProjectRole → RoleInterest → ProjectMembership
```

`ProjectRole` описывает специализацию и задачи внутри проекта, а не единственное свободное место. `RoleInterest` представляет как отклик участника, так и приглашение владельца. `ProjectMembership` фиксирует участие и создаётся только после принятия заявки или приглашения.

Подробности и инварианты: [Domain model](docs/DOMAIN_MODEL.md).

## Структура проекта

```text
teamlab_backend/     Django-проект, приложения и management commands
tests/               API- и доменные тесты
docs/                архитектура, доменная модель и API-документация
postman_collection/  коллекция и локальное окружение Postman
```

Основные Django apps:

- `users` — пользователи, профили, навыки, портфолио и избранное;
- `projects` — проекты, роли, заявки, приглашения и участие;
- `api` — serializers, filters, views, маршруты и demo seed.

## Локальный запуск

Требуется установленный Python.

```bash
git clone https://github.com/IhuliR/teamlab_backend.git
cd teamlab_backend

python -m venv venv
source venv/bin/activate
pip install -r teamlab_backend/requirements.txt
```

Для Windows команда активации окружения:

```powershell
.\venv\Scripts\Activate.ps1
```

Создайте `.env` в корне репозитория:

```env
DEBUG=True
SECRET_KEY=replace-with-a-local-secret
ALLOWED_HOSTS=localhost,127.0.0.1
```

Подготовьте базу и запустите backend:

```bash
python teamlab_backend/manage.py migrate
python teamlab_backend/manage.py seed_demo_data
python teamlab_backend/manage.py runserver
```

`seed_demo_data` создаёт воспроизводимый набор данных для локальной разработки, frontend-интеграции и Postman. Локальные demo credentials:

```text
demo_owner / DemoPass123!
demo_backend / DemoPass123!
demo_designer / DemoPass123!
demo_member / DemoPass123!
```

## API

Локальный base URL: `http://127.0.0.1:8000/api/v1`.

API сгруппирован вокруг auth, users, projects, project roles, dictionaries, role interests и memberships. Основные переходы состояния оформлены отдельными action endpoints:

```text
POST /api/v1/role-interests/{interest_id}/accept/
POST /api/v1/role-interests/{interest_id}/reject/
POST /api/v1/project-memberships/{membership_id}/leave/
POST /api/v1/project-memberships/{membership_id}/remove/
```

Полное описание ресурсов и параметров находится в [API guide](docs/API_GUIDE.md) и [OpenAPI schema](docs/api/teamlab_api_schema_8.yml). После локального запуска схема также доступна через ReDoc: `http://127.0.0.1:8000/redoc/`.

## Тестирование

Из корня репозитория:

```bash
pytest
```

Тесты проверяют auth и JWT rotation, публичные и приватные представления, ownership и permissions, фильтрацию, applications/invitations, переход к membership, портфолио и избранное.

## Документация

- [Project overview](docs/PROJECT_OVERVIEW.md)
- [Domain model](docs/DOMAIN_MODEL.md)
- [Backend architecture](docs/ARCHITECTURE.md)
- [API guide](docs/API_GUIDE.md)
- [Frontend integration](docs/FRONTEND_INTEGRATION.md)
- [OpenAPI schema](docs/api/teamlab_api_schema_8.yml)
- [Postman collection](postman_collection/teamlab.postman_collection.json)
