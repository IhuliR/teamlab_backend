# TeamLab

TeamLab — платформа для поиска и формирования команд под pet-, учебные и некоммерческие проекты.

Платформа помогает:

* owner собрать команду под идею;
* participant найти проект для участия;
* получить практический опыт, портфолио-кейсы и командную работу.

Основной MVP-поток:

```text
Project -> ProjectRole -> RoleInterest -> ProjectMembership
```

---

## 1. Описание проекта

TeamLab — веб-платформа для подбора и формирования проектных команд.

Она предназначена для двух типов пользователей:

* **owner** — создаёт проекты, описывает роли и собирает команду;
* **participant** — ищет проекты, откликается на подходящие роли и участвует в командах.

Ключевая задача TeamLab — связать роли проекта и подходящих людей через управляемый процесс заявок, приглашений и принятия решений.

---

## 2. MVP-возможности

В MVP входят:

* регистрация и JWT-аутентификация;
* публичные каталоги проектов и пользователей;
* создание и редактирование проектов;
* создание ролей проекта;
* заявки participant в проекты;
* приглашения owner пользователям;
* принятие и отклонение заявок/приглашений;
* создание участия в проекте после accepted RoleInterest;
* выход участника из проекта;
* удаление участника owner-ом;
* профиль пользователя;
* навыки пользователя;
* работы портфолио;
* избранные проекты;
* featured projects для главной;
* featured fields для главной;
* read-only уведомления на основе pending RoleInterest.

В MVP не входят:

* отдельная Notification-модель;
* отдельная Invitation-модель;
* отдельная Match-модель;
* cancel/retry/reopen flow для заявок;
* удаление аккаунта;
* глобальный `/search/` endpoint.

---

## 3. Ключевая доменная модель

### Project

Проект, созданный owner-ом.

В списке проектов возвращается краткая карточка с `roles_preview`.
В деталке проекта возвращаются полные `roles` и context-поля текущего пользователя:

* `matching_role_id`;
* `matching_role_name`;
* `my_interest_id`;
* `my_interest_status`;
* `my_interest_source`;
* `my_membership_id`;
* `my_membership_status`.

Для anonymous пользователя context-поля возвращаются как `null`.

### ProjectRole

Роль, специализация или направление внутри проекта.

Важно: `ProjectRole` — это не одно место. На одну роль может быть несколько участников.

В одном проекте не может быть две `ProjectRole` с одной `specialization`.

### RoleInterest

Единая модель для заявок и приглашений.

```text
source = application | invitation
status = pending | accepted | rejected
```

Публичный язык API:

* `applications` — заявки participant в проект;
* `invitations` — приглашения owner пользователям;
* `notifications` — read-only представление pending RoleInterest.

Повторные заявки/приглашения для той же пары `user + project_role` в MVP не поддерживаются.

### ProjectMembership

Факт участия пользователя в проекте.

Создаётся только после accepted RoleInterest.
Напрямую через публичный `POST /project-memberships/` не создаётся.

Завершение участия выполняется через action endpoints:

* `POST /project-memberships/{membership_id}/leave/`;
* `POST /project-memberships/{membership_id}/remove/`.

---

## 4. Технологии

* Python;
* Django;
* Django REST Framework;
* Simple JWT;
* django-filter;
* django-cors-headers;
* SQLite для локальной разработки;
* PostgreSQL как целевая реляционная БД для production-like окружения.

Актуальные версии зависимостей см. в `requirements.txt`.

---

## 5. Быстрый старт backend

### 1. Клонировать репозиторий

```bash
git clone <REPOSITORY_URL>
cd teamlab_backend
```

### 2. Создать и активировать виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate
```

Для Windows:

```bash
venv\Scripts\activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Создать `.env`

В корне проекта рядом с backend-кодом создайте файл `.env`.

Пример:

```env
DEBUG=True
SECRET_KEY=dev-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Выполнить миграции

```bash
python manage.py migrate
```

### 6. Создать демо-данные

```bash
python manage.py seed_demo_data
```

Команда создаёт стабильный набор данных для локальной разработки, frontend-интеграции и Postman-проверок.

Демо-пользователи:

```text
demo_owner / DemoPass123!
demo_backend / DemoPass123!
demo_designer / DemoPass123!
demo_member / DemoPass123!
```

### 7. Запустить сервер

```bash
python manage.py runserver
```

Backend будет доступен по адресу:

```text
http://127.0.0.1:8000
```

Base URL API:

```text
http://127.0.0.1:8000/api/v1
```

---

## 6. Frontend-интеграция

Для локальной frontend-интеграции backend уже настроен на CORS для типовых dev-портов:

```text
http://localhost:3000
http://127.0.0.1:3000
http://localhost:5173
http://127.0.0.1:5173
```

Если frontend запускается на другом порту, его нужно добавить в `CORS_ALLOWED_ORIGINS` в `settings.py`.

Рекомендуемый порядок запуска:

```bash
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

После этого frontend может использовать демо-аккаунты и обращаться к API по base URL:

```text
http://127.0.0.1:8000/api/v1
```

---

## 7. Postman

В проекте есть Postman collection и environment для проверки API на seed-данных:

```text
postman_collection/teamlab.postman_collection.json
postman_collection/teamlab.postman_environment.json
```

Как использовать:

1. Импортировать оба файла в Postman.
2. Выбрать environment `TeamLab Local Seeded Demo Environment`.
3. Убедиться, что backend запущен.
4. Выполнить:

```bash
python manage.py seed_demo_data
```

5. В Postman сначала запустить папку:

```text
00 Setup / Auth
```

Она логинит демо-пользователей и сохраняет токены/ID в environment.
Refresh request заменяет в environment оба backend-токена: новый `access`
и новый `refresh`.

После этого можно запускать остальные папки коллекции.

Некоторые запросы меняют состояние базы:

* accept/reject RoleInterest;
* leave/remove ProjectMembership;
* DELETE portfolio work;
* DELETE favorite project.

Если состояние демо-данных изменилось, можно снова выполнить:

```bash
python manage.py seed_demo_data
```

---

## 8. API и документация

Актуальный OpenAPI-контракт:

```text
docs/api/teamlab_api_schema_8.yml
```

Основные документы:

* `docs/PROJECT_OVERVIEW.md` — общий обзор проекта;
* `docs/DOMAIN_MODEL.md` — доменная модель и инварианты;
* `docs/ARCHITECTURE.md` — архитектурные решения backend-а;
* `docs/API_GUIDE.md` — REST API, сценарии и endpoints;
* `docs/FRONTEND_INTEGRATION.md` — краткая карта интеграции frontend-а с API;
* `docs/STYLE_GUIDE.md` — правила разработки;
* `docs/FAQ.md` — ответы на частые вопросы;
* `docs/AGENTS.md` — контрольные правила и типовые риски.

OpenAPI-контракт является главным источником истины по публичному API.

---

## 9. Основные endpoints

### Auth

```text
POST /api/v1/auth/token/login/
POST /api/v1/auth/token/refresh/
```

Login выполняется по `username + password`.
`POST /api/v1/auth/token/refresh/` возвращает новую пару `access + refresh`
и `user`. После успешного refresh клиент должен сохранить оба новых токена:
старый refresh token повторно использовать нельзя.

### Projects

```text
GET    /api/v1/projects/
GET    /api/v1/projects/featured/
POST   /api/v1/projects/
GET    /api/v1/projects/{project_id}/
PATCH  /api/v1/projects/{project_id}/
GET    /api/v1/projects/{project_id}/applications/
POST   /api/v1/projects/{project_id}/applications/
GET    /api/v1/projects/{project_id}/invitations/
POST   /api/v1/projects/{project_id}/invitations/
```

### Users

```text
GET    /api/v1/users/
POST   /api/v1/users/
GET    /api/v1/users/{user_id}/
GET    /api/v1/users/me/
PATCH  /api/v1/users/me/
GET    /api/v1/users/me/projects/
GET    /api/v1/users/me/applications/
GET    /api/v1/users/me/notifications/
```

### RoleInterest actions

```text
POST /api/v1/role-interests/{interest_id}/accept/
POST /api/v1/role-interests/{interest_id}/reject/
```

### ProjectMembership actions

```text
POST /api/v1/project-memberships/{membership_id}/leave/
POST /api/v1/project-memberships/{membership_id}/remove/
```

### Dictionaries

```text
GET  /api/v1/fields/
GET  /api/v1/fields/featured/
GET  /api/v1/specializations/
GET  /api/v1/skills/
```

`Field`, `Specialization` и `Skill` управляются через админку/seed/служебные инструменты.
Публичный API отдаёт эти справочники только на чтение. `GET /api/v1/skills/`
поддерживает фильтр `field_ids`.

---

## 10. Поиск и фильтрация

Поиск в MVP контекстный:

```text
GET /api/v1/projects/?search=...
GET /api/v1/users/?search=...
```

Глобального `/search/` endpoint в MVP нет.

### Projects filters

```text
search
field_id
field_ids
status
specialization_ids
skill_ids
ordering
```

### Users filters

```text
search
account_type
field_id
field_ids
specialization_ids
skill_ids
level
work_format
employment_type
search_status
city
ordering
```

Multi-value filters вроде `field_ids`, `skill_ids` и `specialization_ids`
передаются comma-separated списком. `city` — свободная строка профиля, а не
backend-справочник.

---

## 11. Архитектурные ограничения MVP

* `ProjectRole` — не одно место, а направление внутри проекта.
* На одну `ProjectRole` может быть несколько участников.
* В одном проекте нет двух `ProjectRole` с одной `specialization`.
* `ProjectRole.is_open` отсутствует.
* `RoleInterest` уникален для пары `user + project_role`.
* Повторные applications/invitations для той же пары не поддерживаются.
* `ProjectMembership` создаётся только через accepted RoleInterest.
* `ProjectMembership` не создаётся напрямую публичным API.
* `leave/remove` реализованы action endpoints, а не PATCH status.
* `Notification`, `Invitation`, `IncomingInterest`, `Match` не являются отдельными моделями MVP.
* `cancel/cancelled`, `retry`, `reopen` не входят в MVP.
* `DELETE /api/v1/users/me/` не входит в MVP.

---

## 12. Статус проекта

MVP, активная разработка.

Текущий backend готов к первичной frontend-интеграции через актуальный OpenAPI-контракт, seed-данные и Postman collection.
