# API_GUIDE.md

## 1. Общая идея API

TeamLab API — это RESTful сервис для создания и управления проектами и формирования команд. Основной поток работы: владелец создаёт проект, добавляет в него роли, участники откликаются на эти роли или получают приглашения, после принятия interest формируется участие в проекте (ProjectMembership). API позволяет работать с основными сущностями системы: `User`, `Project`, `ProjectRole`, `RoleInterest`, `ProjectMembership` и `FavoriteProject`.

API построено на HTTPS/JSON с авторизацией по JWT-токенам. Каждое действие через API отражает бизнес-логику доменной модели TeamLab: создание проектов, ролей, заявок на участие и т.д.

Актуальный API-контракт использует префикс `/api/v1/...`. OpenAPI-схема является источником истины для endpoints, request/response schemas, HTTP-кодов и API-visible полей.

## 2. Основные сценарии

### Регистрация и авторизация

1. **Регистрация.** Фронтенд вызывает `POST /api/v1/users/` с `username`, `email`, `password`, `account_type` (`owner` или `participant`). В ответе `201` возвращается созданный пользователь: `id`, `username`, `email`, `account_type`.
2. **Авторизация.** Фронтенд отправляет `POST /api/v1/auth/token/login/` с `email` и `password`. В ответе `200` приходит `access`, `refresh` и `user` (`id`, `username`, `account_type`).
3. **Обновление токена.** Фронтенд отправляет `POST /api/v1/auth/token/refresh/` с `refresh`. В ответе `200` приходит новый `access` и данные `user` по контракту.

`access` нужно передавать в заголовке защищённых запросов:

```http
Authorization: Bearer <access>
```

### Создание проекта

Владелец (`account_type = owner`) создаёт новый проект через `POST /api/v1/projects/`, передавая `field_id`, `title`, `description` и опциональные `idea`, `benefits`. В ответе `201` API возвращает `ProjectDetail`. Получение проекта: `GET /api/v1/projects/{project_id}/`. Список проектов текущего пользователя: `GET /api/v1/users/me/projects/`. Проект создаётся со статусом `open`.

### Создание роли в проекте

Владелец проекта добавляет роль вызовом `POST /api/v1/project-roles/`. В теле запроса указываются `project_id`, `specialization_id`, `description`, `capacity`. Новая роль создаётся с `is_open = true`. Роли можно получить через `GET /api/v1/project-roles/?project_id={project_id}` или `GET /api/v1/project-roles/{role_id}/`.

### Отклик на роль (RoleInterest)

Пользователь-участник (`participant`) откликается на роль вызовом `POST /api/v1/project-roles/{role_id}/interests/`. Request body отсутствует. Сервер проверяет, что проект и роль открыты, и что для пары `(user, project_role)` ещё нет существующего **RoleInterest**. Если всё верно, создаётся объект **RoleInterest** со `source = application` и статусом `pending`.

### Приглашение на роль (invite)

Владелец проекта приглашает участника на роль через `POST /api/v1/project-roles/{role_id}/invite/` с телом:

```json
{
  "user_id": 2
}
```

При invite создаётся `RoleInterest` со `source = invitation` и `status = pending`. Отдельная модель `Invitation` не создаётся. Создавать invitation может только владелец проекта, а принять или отклонить invitation может только приглашённый пользователь.

### Принятие или отклонение RoleInterest

Для `source = application` владелец проекта принимает или отклоняет отклик. Для `source = invitation` приглашённый участник принимает или отклоняет invitation.

- `POST /api/v1/role-interests/{interest_id}/accept/` переводит RoleInterest в `accepted` и возвращает созданный **ProjectMembership**.
- `POST /api/v1/role-interests/{interest_id}/reject/` переводит RoleInterest в `rejected` и возвращает обновлённый **RoleInterest**.

PATCH status flow для RoleInterest в актуальном API-контракте не используется.

### Участие в проекте (ProjectMembership)

После принятия interest появляется запись **ProjectMembership** со `status = active`. Фронтенд получает участия через `GET /api/v1/project-memberships/` с фильтрами `project_id`, `project_role_id`, `user_id`, `status`. Создание ProjectMembership напрямую через API отсутствует.

Завершение участия выполняется через `PATCH /api/v1/project-memberships/{membership_id}/` с `status = left` или `status = removed`. Этот endpoint не создаёт membership и не меняет `accepted_interest_id`.

Контакты пользователя доступны только если существует `ProjectMembership.status = active`. До активного участия контакты скрыты.

### Работа с избранным

Пользователь-участник добавляет проект в избранное вызовом `POST /api/v1/users/me/favorite-projects/` с `project_id`. Создаётся **FavoriteProject** (`user_id`, `project_id`). Удаление выполняется через `DELETE /api/v1/users/me/favorite-projects/{project_id}/`. Список избранных проектов: `GET /api/v1/users/me/favorite-projects/`.

Избранное существует только для проектов участника. Избранного участников для владельца проекта в MVP нет.

### Уведомления

В MVP уведомления не являются отдельной бизнес-сущностью и не имеют собственного API. Фронтенд показывает их как агрегированное представление данных из **RoleInterest** и **ProjectMembership**: новые отклики, приглашения, изменения статуса interest и изменения участия.

## 3. Ключевые сущности API

- **User:** единственная сущность пользователя и его профиля. API-visible поля публичного профиля: `id`, `username`, `bio`, `account_type`, `specialization_id`, `level`, `workload_hours_per_week`, `work_format`, `city`, `avatar`, `created_at`, `updated_at`, `skills`, `portfolio_works`. Для текущего пользователя дополнительно возвращается `email`.
- **UserSkill:** `id`, `user_id`, `skill_id`, `level`, `created_at`, `updated_at`.
- **PortfolioWork:** `id`, `user_id`, `title`, `task`, `solution`, `image`, `technologies`, `link`, `created_at`, `updated_at`.
- **Project:** `id`, `owner_id`, `field_id`, `title`, `description`, `idea`, `benefits`, `status`, `created_at`, `updated_at`.
- **ProjectRole:** `id`, `project_id`, `specialization_id`, `description`, `capacity`, `is_open`, `created_at`, `updated_at`.
- **RoleInterest:** `id`, `user_id`, `project_role_id`, `source`, `status`, `reviewed_at`, `created_at`, `updated_at`.
- **ProjectMembership:** `id`, `user_id`, `project_role_id`, `accepted_interest_id`, `status`, `joined_at`, `ended_at`, `created_at`, `updated_at`.
- **FavoriteProject:** `id`, `user_id`, `project_id`, `created_at`.

## 4. Endpoint reference

### Users and auth

| Endpoint | Method | Request | Response | Codes |
|---|---:|---|---|---|
| `/api/v1/users/` | GET | query: `page`, `limit`, `level`, `account_type` | `PaginatedUsers` (`count`, `next`, `previous`, `results`) | 200, 400 |
| `/api/v1/users/` | POST | `UserCreateRequest`: required `username`, `email`, `password`, `account_type` | `UserCreatedResponse` | 201, 400 |
| `/api/v1/users/{user_id}/` | GET | path `user_id` | `UserPublic` | 200, 404 |
| `/api/v1/users/me/` | GET | Bearer token | `CurrentUser` | 200, 401 |
| `/api/v1/users/me/` | PATCH | `UserUpdateRequest`: optional `username`, `bio`, `specialization_id`, `level`, `workload_hours_per_week`, `work_format`, `city`, `skills` | `CurrentUser` | 200, 400, 401 |
| `/api/v1/users/me/avatar/` | PUT | `AvatarUpdateRequest`: required `avatar` | `AvatarResponse` | 200, 400, 401 |
| `/api/v1/users/me/avatar/` | DELETE | Bearer token | empty body | 204, 401 |
| `/api/v1/users/set_password/` | POST | required `new_password`, `current_password` | empty body | 204, 400, 401 |
| `/api/v1/auth/token/login/` | POST | required `email`, `password` | `access`, `refresh`, `user` | 200, 400, 401 |
| `/api/v1/auth/token/refresh/` | POST | required `refresh` | `access`, `user` | 200, 401 |

`account_type` не изменяется через пользовательский интерфейс и отсутствует в `UserUpdateRequest`.

### Dictionaries

| Endpoint | Method | Request | Response | Codes |
|---|---:|---|---|---|
| `/api/v1/skills/` | GET | query: `search`, `ordering` | array of `Skill` | 200 |
| `/api/v1/skills/` | POST | `SkillCreateRequest`: required `name` | `Skill` | 201, 400, 401, 403 |
| `/api/v1/specializations/` | GET | query: `search`, `field_id` | array of `Specialization` | 200 |
| `/api/v1/specializations/` | POST | required `field_id`, `name` | `Specialization` | 201, 400, 401, 403 |
| `/api/v1/fields/` | GET | query: `search` | array of `Field` | 200 |
| `/api/v1/fields/` | POST | required `name` | `Field` | 201, 400, 401, 403 |

### Projects and roles

| Endpoint | Method | Request | Response | Codes |
|---|---:|---|---|---|
| `/api/v1/projects/` | GET | query: `page`, `limit`, `status`, `field_id` | `PaginatedProjects` | 200, 400 |
| `/api/v1/projects/` | POST | required `field_id`, `title`, `description`; optional `idea`, `benefits` | `ProjectDetail` | 201, 400, 401 |
| `/api/v1/projects/{project_id}/` | GET | path `project_id` | `ProjectDetail` | 200, 404 |
| `/api/v1/projects/{project_id}/` | PATCH | optional `field_id`, `title`, `description`, `idea`, `benefits`, `status` | `ProjectDetail` | 200, 400, 401, 403, 404 |
| `/api/v1/project-roles/` | GET | query: `project_id`, `specialization_id`, `is_open` | `ProjectRolesListResponse` with `results` | 200, 404 |
| `/api/v1/project-roles/` | POST | required `project_id`, `specialization_id`, `description`, `capacity` | `ProjectRole` | 201, 400, 401, 403, 404 |
| `/api/v1/project-roles/{role_id}/` | GET | path `role_id` | `ProjectRole` | 200, 404 |
| `/api/v1/project-roles/{role_id}/` | PATCH | optional `specialization_id`, `description`, `capacity`, `is_open` | `ProjectRole` | 200, 400, 401, 403, 404 |

### Role interests and memberships

| Endpoint | Method | Request | Response | Codes |
|---|---:|---|---|---|
| `/api/v1/role-interests/` | GET | query: `project_role_id`, `user_id`, `source`, `status` | array of `RoleInterest` | 200, 401, 403 |
| `/api/v1/project-roles/{role_id}/interests/` | POST | path `role_id`; no request body | `RoleInterest` | 201, 400, 401, 403, 404, 409 |
| `/api/v1/project-roles/{role_id}/invite/` | POST | required `user_id` | `RoleInterest` | 201, 400, 401, 403, 404, 409 |
| `/api/v1/role-interests/{interest_id}/accept/` | POST | path `interest_id`; no request body | `ProjectMembership` | 200, 400, 401, 403, 404, 409 |
| `/api/v1/role-interests/{interest_id}/reject/` | POST | path `interest_id`; no request body | `RoleInterest` | 200, 400, 401, 403, 404 |
| `/api/v1/project-memberships/` | GET | query: `project_id`, `project_role_id`, `user_id`, `status` | array of `ProjectMembership` | 200, 401 |
| `/api/v1/project-memberships/{membership_id}/` | PATCH | required `status` = `left` or `removed` | `ProjectMembership` | 200, 400, 401, 403, 404 |

### Current user resources

| Endpoint | Method | Request | Response | Codes |
|---|---:|---|---|---|
| `/api/v1/users/me/projects/` | GET | query: `page`, `limit`, `status`, `relation` | `PaginatedMyProjects` | 200, 401 |
| `/api/v1/users/me/interests/` | GET | query: `page`, `limit`, `status` | `PaginatedMyInterests` | 200, 401 |
| `/api/v1/users/me/portfolio-works/` | GET | Bearer token | array of `PortfolioWork` | 200, 401 |
| `/api/v1/users/me/portfolio-works/` | POST | required `title`; optional `task`, `solution`, `image`, `technologies`, `link` | `PortfolioWork` | 201, 400, 401 |
| `/api/v1/users/me/portfolio-works/{portfolio_work_id}/` | PATCH | optional `title`, `task`, `solution`, `image`, `technologies`, `link` | `PortfolioWork` | 200, 400, 401, 404 |
| `/api/v1/users/me/portfolio-works/{portfolio_work_id}/` | DELETE | path `portfolio_work_id` | empty body | 204, 401, 404 |
| `/api/v1/users/me/favorite-projects/` | GET | Bearer token | array of `FavoriteProject` | 200, 401 |
| `/api/v1/users/me/favorite-projects/` | POST | required `project_id` | `FavoriteProject` | 201, 400, 401, 403, 409 |
| `/api/v1/users/me/favorite-projects/{project_id}/` | DELETE | path `project_id` | empty body | 204, 401, 404 |

## 5. Важные правила API

- **RoleInterest ≠ ProjectMembership.** Отклик и участие — разные сущности: отклик создаётся первым (`pending`), а участие появляется только после его принятия.
- **Участие создаётся только через отклик.** Нельзя создать ProjectMembership без существующего accepted RoleInterest.
- **Invite создаётся через RoleInterest.** Отдельная сущность Invitation не создаётся; invitation отличается `RoleInterest.source = invitation`.
- **Контакты открываются только после участия.** До `ProjectMembership.status = active` контакты пользователя скрыты.
- **Один пользователь — один тип аккаунта.** В MVP `account_type` задаётся при регистрации и не меняется через пользовательский интерфейс.
- **Одна специализация у пользователя.** Каждый пользователь связан с одной специализацией (`specialization_id`), если она заполнена.
- **Избранное есть только у участника.** `FavoriteProject` используется только когда `account_type = participant`.
- **Уведомления — UI-представление.** Отдельная бизнес-сущность Notification и отдельный notification API в MVP не используются.

## 6. Авторизация

TeamLab API использует JWT-токены. После входа (`POST /api/v1/auth/token/login/`) фронтенд получает `access`, `refresh` и `user`. Защищённые запросы используют:

```http
Authorization: Bearer <access>
```

- **Неавторизованные запросы:** без токена или с неверным токеном защищённые endpoint возвращают 401 Unauthorized.
- **Права доступа по типу аккаунта:** некоторые операции доступны только определённому аккаунту или связанному пользователю. Если пользователь пытается выполнить недоступную операцию, API возвращает 403 Forbidden.

## 7. Ошибки и ответы

API возвращает JSON-ответы. В случае ошибки приходит HTTP-код и сообщение. Типичные коды:
- **400 Bad Request:** неверные или неполные данные, некорректное состояние объекта, закрытый проект/роль и т.п.
- **401 Unauthorized:** нет токена, токен недействителен или истёк.
- **403 Forbidden:** пользователь авторизован, но не имеет прав.
- **404 Not Found:** ресурс не найден.
- **409 Conflict:** конфликт бизнес-правил, например существующий `RoleInterest` для пары `(user, project_role)` или уже добавленный в избранное проект.

Типовой формат ошибки:

```json
{
  "detail": "Недостаточно прав."
}
```

Ошибка валидации может возвращаться как объект, где ключи соответствуют именам полей:

```json
{
  "field": ["Обязательное поле."],
  "non_field_errors": ["Некорректное состояние объекта."]
}
```

## 8. Ограничения MVP

- **Нет восстановления пароля.** Эндпоинтов для сброса пароля нет; `POST /api/v1/users/set_password/` меняет пароль только в авторизованном состоянии.
- **Нет email-уведомлений.** Никаких писем не отправляется.
- **Нет Notification-модели.** Уведомления строятся во фронтенде как агрегат данных из `RoleInterest` и `ProjectMembership`.
- **Нет сложного matching.** Нет автоматического подбора участников или рекомендаций; вся логика основана на действиях пользователей и фильтрации по структурированным данным.
- **Нет дублей RoleInterest.** Для пары `(user, project_role)` может существовать только один `RoleInterest`.
- **Один тип аккаунта.** Пользователь выбирает `account_type` при регистрации и не меняет его через пользовательский интерфейс.

## 9. Практические рекомендации

- **Content-Type и JSON:** всегда передавайте заголовок `Content-Type: application/json` и формируйте JSON по OpenAPI-контракту.
- **JWT-токен в заголовке:** используйте `Authorization: Bearer <access>` для защищённых вызовов.
- **Статусы проекта/роли:** перед отправкой отклика убедитесь, что проект (`status = open`) и роль (`is_open = true`) открыты.
- **Проверка capacity:** после принятия заявки роль может закрыться, если достигнут лимит `capacity`.
- **Тип аккаунта:** проверяйте `account_type` пользователя перед вызовом endpoint, доступных только owner или participant.
- **Обработка ошибок:** анализируйте `detail` или объект ошибок валидации.
- **Уведомления:** показывайте новые события как агрегат данных из `RoleInterest` и `ProjectMembership`, без вызова отдельного notification API.
- **Соответствие сценариям:** не пытайтесь обходить логику: нельзя создавать ProjectMembership напрямую или менять `accepted_interest_id` вручную.
