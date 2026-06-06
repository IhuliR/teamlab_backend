# Frontend Integration Guide

## 1. Для чего этот файл

Это короткий frontend cheat sheet по интеграции с TeamLab API. Полный API shape см. в OpenAPI-контракте `docs/api/teamlab_api_schema_8.yml`, доменные правила - в `docs/DOMAIN_MODEL.md`, подробные сценарии API - в `docs/API_GUIDE.md`.

Файл не заменяет контракт. Он показывает, какие endpoints нужны основным экранам, какие состояния рисовать в интерфейсе и какие MVP-действия не вызывать.

## 2. Быстрый локальный запуск

Из корня backend-проекта:

```bash
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

`seed_demo_data` создает стабильные данные для локальной разработки, frontend-интеграции и Postman-проверок. Миграции здесь только запускаются вручную разработчиком; этот guide не требует менять migrations.

## 3. Base URL и окружение

Локальный API base URL:

```text
http://127.0.0.1:8000/api/v1
```

Backend уже настроен на CORS для типовых frontend dev origins:

```text
http://localhost:3000
http://127.0.0.1:3000
http://localhost:5173
http://127.0.0.1:5173
```

Если frontend запускается на другом порту, origin нужно добавить в `CORS_ALLOWED_ORIGINS` в backend settings.

## 4. Демо-пользователи

```text
demo_owner / DemoPass123!
demo_backend / DemoPass123!
demo_designer / DemoPass123!
demo_member / DemoPass123!
```

Роли в seed-flow:

- `demo_owner` - owner демо-проекта.
- `demo_backend` - participant с pending application и favorite project.
- `demo_designer` - participant с pending invitation и portfolio work.
- `demo_member` - participant с active membership.

## 5. Авторизация

Login выполняется по `username + password`, email не используется как login identifier.

```http
POST /api/v1/auth/token/login/
```

```json
{
  "username": "demo_owner",
  "password": "DemoPass123!"
}
```

Компактный пример response:

```json
{
  "access": "<jwt-access>",
  "refresh": "<jwt-refresh>",
  "user": {
    "id": 1,
    "username": "demo_owner",
    "display_name": "Demo Owner",
    "account_type": "owner"
  }
}
```

`username` - логин. `display_name` - отображаемое имя в интерфейсе. Для authenticated requests передавайте:

```http
Authorization: Bearer <access>
```

Refresh:

```http
POST /api/v1/auth/token/refresh/
```

```json
{
  "refresh": "<current-jwt-refresh>"
}
```

Успешный response имеет ту же auth-форму: новый `access`, новый `refresh`
и `user`. После каждого успешного refresh frontend должен атомарно сохранить
оба новых токена. Старый refresh token после rotation повторно использовать
нельзя.

## 6. Роли пользователей в интерфейсе

### Anonymous

Может смотреть проекты, участников, справочники, project detail и public user detail. Не может откликаться, добавлять в избранное, редактировать профиль, создавать проекты, принимать или отклонять заявки/приглашения.

### Participant

Может откликнуться на проект, принять/отклонить invitation, покинуть проект, вести профиль и портфолио, добавлять проекты в избранное.

### Owner

Может создавать/редактировать проекты, создавать/редактировать/удалять роли, смотреть project applications/invitations, приглашать пользователей, принимать/отклонять applications, удалять участника из проекта.

## 7. Основные экраны и endpoints

| Экран / сценарий | Endpoint | Метод | Для кого | Комментарий |
| --- | --- | --- | --- | --- |
| Главная: проекты недели | `/projects/featured/` | GET | все | Карточки проектов как в `/projects/`. |
| Главная: направления | `/fields/featured/` | GET | все | "Все профили" - синтетическая frontend-карточка. |
| Все проекты | `/projects/` | GET | все | Фильтры: `search`, `field_id`, `status`, `specialization_ids`, `skill_ids`, `ordering`. |
| Project detail | `/projects/{project_id}/` | GET | все | Полные `roles` и context fields текущего пользователя. |
| Отклик на проект | `/projects/{project_id}/applications/` | POST | participant | Body отсутствует. Backend выбирает matching role. |
| Participant profile | `/users/me/` | GET/PATCH | participant | Текущий профиль и настройки. |
| Мои проекты | `/users/me/projects/` | GET | participant | Active memberships и pending invitations. |
| Мои заявки | `/users/me/applications/` | GET | participant | Applications текущего пользователя. |
| Мои уведомления | `/users/me/notifications/` | GET | auth | Pending invitations для participant, pending applications для owner. |
| Портфолио | `/users/me/portfolio-works/` | GET/POST | participant | Работы портфолио. |
| Работа портфолио | `/users/me/portfolio-works/{portfolio_work_id}/` | PATCH/DELETE | participant | Редактирование/удаление своей работы. |
| Избранное | `/users/me/favorite-projects/` | GET/POST | participant | GET возвращает favorite record + project card. |
| Удалить из избранного | `/users/me/favorite-projects/{project_id}/` | DELETE | participant | `project_id`, не favorite id. |
| Owner profile | `/users/me/` | GET/PATCH | owner | `owned_project_ids` помогают выбрать проекты owner-а. |
| Заявки проекта | `/projects/{project_id}/applications/` | GET | owner | Только для owner проекта. |
| Приглашения проекта | `/projects/{project_id}/invitations/` | GET | owner | Pending outgoing invitations. |
| Создать приглашение | `/projects/{project_id}/invitations/` | POST | owner | Body: `{ "user_id": 2 }`. |
| Принять RoleInterest | `/role-interests/{interest_id}/accept/` | POST | owner/participant | Owner принимает application, participant принимает invitation. |
| Отклонить RoleInterest | `/role-interests/{interest_id}/reject/` | POST | owner/participant | Правила такие же, как у accept. |
| Удалить участника | `/project-memberships/{membership_id}/remove/` | POST | owner | Завершает membership со статусом `removed`. |
| Участники | `/users/` | GET | все | Фильтры: `search`, `field_id`, `specialization_ids`, `skill_ids`, `level`, `work_format`, `employment_type`, `search_status`, `city`, `ordering`. |
| User detail | `/users/{user_id}/` | GET | все | Public profile без email и приватных настроек. |
| Fields | `/fields/` | GET | все | Системный справочник. |
| Specializations | `/specializations/` | GET | все | Системный справочник. |
| Skills | `/skills/` | GET | все | Справочник навыков. |
| Create skill | `/skills/` | POST | auth | Единственный публично расширяемый справочник. |

## 8. Поиск и подсказки

Отдельного глобального `/search/` endpoint в MVP нет. Поиск контекстный:

```text
GET /projects/?search=...
GET /users/?search=...
```

Подсказки в search dropdown - это suggestions, а не backend search results. В MVP frontend может собирать их из:

- `GET /fields/`;
- `GET /specializations/`;
- `GET /skills/`;
- фиксированного frontend-списка, если это нужно для UX.

Backend search endpoint вызывается после ввода/применения поиска.

```text
Пользователь выбрал подсказку "графический дизайнер" -> frontend вызывает:
GET /projects/?search=графический%20дизайнер
или
GET /users/?search=графический%20дизайнер
в зависимости от текущего раздела.
```

## 9. Project detail и кнопка "Хочу работать"

Для anonymous `GET /projects/{project_id}/` возвращает context fields как `null`. Фрагмент response:

```json
{
  "id": 1,
  "title": "Демо-проект TeamLab",
  "is_favorited": false,
  "roles": [],
  "matching_role_id": null,
  "matching_role_name": null,
  "my_interest_id": null,
  "my_interest_status": null,
  "my_interest_source": null,
  "my_membership_id": null,
  "my_membership_status": null
}
```

Anonymous-кнопка "Хочу работать" не вызывает POST. Она ведет в auth-flow; после login frontend может вернуть пользователя на project detail и заново запросить проект.

Для participant frontend смотрит context fields. Фрагмент response:

```json
{
  "id": 1,
  "title": "Демо-проект TeamLab",
  "matching_role_id": 1,
  "matching_role_name": "Backend-разработчик",
  "my_interest_id": 4,
  "my_interest_status": "pending",
  "my_interest_source": "application",
  "my_membership_id": null,
  "my_membership_status": null
}
```

Если можно откликнуться:

```http
POST /api/v1/projects/{project_id}/applications/
```

Request body отсутствует. Owner не откликается на собственный проект.

## 10. Applications / Invitations / Notifications

Applications и invitations - это `RoleInterest`. Отдельной Notification-модели нет; notifications - read-only представление pending RoleInterest.

Participant application:

```http
POST /api/v1/projects/{project_id}/applications/
```

Owner смотрит applications:

```http
GET /api/v1/projects/{project_id}/applications/
```

Owner создает invitation:

```http
POST /api/v1/projects/{project_id}/invitations/
```

```json
{
  "user_id": 2
}
```

Participant смотрит invitations:

```http
GET /api/v1/users/me/projects/
GET /api/v1/users/me/notifications/
```

Фрагмент `GET /users/me/projects/`:

```json
{
  "memberships": [
    {
      "id": 7,
      "project_id": 1,
      "project_title": "Демо-проект TeamLab",
      "project_image": null,
      "project_role_id": 2,
      "project_role_name": "Frontend-разработчик",
      "status": "active"
    }
  ],
  "invitations": [
    {
      "id": 5,
      "project_id": 1,
      "project_title": "Демо-проект TeamLab",
      "project_image": null,
      "project_role_id": 3,
      "project_role_name": "UI/UX-дизайнер",
      "source": "invitation",
      "status": "pending",
      "created_at": "2026-04-24T13:20:00Z",
      "updated_at": "2026-04-24T13:20:00Z"
    }
  ]
}
```

Фрагмент `GET /users/me/notifications/`:

```json
[
  {
    "id": 4,
    "source": "application",
    "status": "pending",
    "user_id": 2,
    "username": "demo_backend",
    "project_id": 1,
    "project_title": "Демо-проект TeamLab",
    "project_role_id": 1,
    "project_role_name": "Backend-разработчик",
    "created_at": "2026-04-24T13:00:00Z"
  }
]
```

Accept/reject:

```http
POST /api/v1/role-interests/{interest_id}/accept/
POST /api/v1/role-interests/{interest_id}/reject/
```

Правила:

- `application` принимает/отклоняет owner проекта.
- `invitation` принимает/отклоняет приглашенный participant.
- `accept` создает membership.
- `reject` не создает membership.

## 11. Membership actions: leave/remove

```http
POST /api/v1/project-memberships/{membership_id}/leave/
POST /api/v1/project-memberships/{membership_id}/remove/
```

Правила:

- `leave` вызывает сам участник.
- `remove` вызывает owner проекта.
- Прямого `PATCH membership status` нет.
- Прямого `POST /project-memberships/` нет.

## 12. Профиль, портфолио и избранное

Current user profile:

```http
GET /api/v1/users/me/
PATCH /api/v1/users/me/
```

`username` - логин, `display_name` - имя для UI. Participant не может сменить или убрать `specialization_id`, если есть active membership, pending application или pending invitation. Frontend может заранее показать warning, но backend все равно является источником истины и вернет ошибку.

Public user profile:

```http
GET /api/v1/users/{user_id}/
```

Public profile не отдает email и private settings. `contacts_visible` вычисляется backend-ом; `social_links` может быть `null`, если контакты скрыты.

Portfolio works:

```http
GET /api/v1/users/me/portfolio-works/
POST /api/v1/users/me/portfolio-works/
PATCH /api/v1/users/me/portfolio-works/{portfolio_work_id}/
DELETE /api/v1/users/me/portfolio-works/{portfolio_work_id}/
```

Favorite projects:

```http
GET /api/v1/users/me/favorite-projects/
POST /api/v1/users/me/favorite-projects/
DELETE /api/v1/users/me/favorite-projects/{project_id}/
```

Favorites предназначены для participant. Повторное добавление может вернуть ошибку. List возвращает favorite record и вложенную карточку проекта. Фрагмент list item:

```json
{
  "id": 1,
  "user_id": 2,
  "project_id": 1,
  "project": {
    "id": 1,
    "title": "Демо-проект TeamLab",
    "image": null,
    "roles_preview": [
      {
        "id": 1,
        "specialization_id": 1,
        "specialization_name": "Backend-разработчик"
      }
    ]
  },
  "created_at": "2026-04-01T10:00:00Z"
}
```

## 13. Частые frontend-состояния

| Состояние | Как понять по API | Что показать |
| --- | --- | --- |
| Anonymous на project detail | `my_interest_*`, `my_membership_*`, `matching_role_*` равны `null` | CTA ведет в login/register. |
| Participant может откликнуться | Есть `matching_role_id`, нет `my_interest_id`, нет active `my_membership_id` | Активная кнопка "Хочу работать". |
| Application уже pending | `my_interest_source = application`, `my_interest_status = pending` | "Заявка отправлена", кнопку заблокировать. |
| Participant уже invited | `my_interest_source = invitation`, `my_interest_status = pending` или invitation в `/users/me/projects/` | Кнопки принять/отклонить приглашение. |
| Participant active member | `my_membership_status = active` или membership в `/users/me/projects/` | Статус участия, действие "Покинуть проект". |
| Owner смотрит pending applications | `GET /projects/{project_id}/applications/` возвращает items со `status = pending` | Список заявок с accept/reject. |
| Нет matching role | `matching_role_id = null` для authenticated participant | Показать, что нет роли под специализацию. |
| Повторная application/invitation | POST возвращает `400 Bad Request` | Показать понятную ошибку, не повторять silently. |
| Role нельзя удалить | `DELETE /project-roles/{role_id}/` возвращает `400 Bad Request` | Объяснить, что есть active участники или pending заявки/приглашения. |
| Specialization нельзя сменить | `PATCH /users/me/` возвращает `400 Bad Request` по `specialization_id` | Показать причину и оставить старое значение. |

## 14. Ошибки, которые нужно обработать

- `401 Unauthorized` - нет или протух token; отправить в login-flow.
- `403 Forbidden` - пользователь не имеет права выполнить действие.
- `400 Bad Request` - доменная валидация: повторная заявка/приглашение, нет matching role, нельзя сменить specialization, нельзя удалить role, дубль specialization в project roles.
- `404 Not Found` - объект не найден или не принадлежит текущему пользователю.
- `405 Method Not Allowed` - endpoint есть, но метод не поддерживается.

`500 Internal Server Error` не должен быть нормальным frontend-состоянием. Если frontend получает 500, это backend bug/report.

## 15. Что не входит в MVP и не нужно вызывать

- `DELETE /users/me/`.
- Global `/search/`.
- Generic `GET /role-interests/`.
- Generic `GET /project-memberships/`.
- Direct `POST /project-memberships/`.
- `PATCH /project-memberships/{id}/`.
- Cancel/retry/reopen заявок и приглашений.
- `POST /fields/`.
- `POST /specializations/`.
- Отдельная Notification/Invitation/Match модель.

## 16. Где смотреть подробности

- `README.md` - запуск, Postman и общий список endpoints.
- `docs/PROJECT_OVERVIEW.md` - обзор продукта и MVP-flow.
- `docs/API_GUIDE.md` - практическое описание API и сценариев.
- `docs/DOMAIN_MODEL.md` - доменные инварианты и lifecycle.
- `docs/FAQ.md` - частые вопросы по MVP-решениям.
- `docs/ARCHITECTURE.md` - архитектурные границы backend-а.
- `docs/STYLE_GUIDE.md` - правила API/backend-стиля.
- `docs/AGENTS.md` - типовые риски и запреты для изменений.
- `docs/api/teamlab_api_schema_8.yml` - главный OpenAPI-контракт.
- `postman_collection/teamlab.postman_collection.json` - demo-flow запросов.
- `postman_collection/teamlab.postman_environment.json` - локальное Postman окружение.
