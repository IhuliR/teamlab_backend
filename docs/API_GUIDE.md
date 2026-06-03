# API_GUIDE.md

## 1. Общая идея API

TeamLab API описывает MVP-поток командообразования:

`Project -> ProjectRole -> RoleInterest -> ProjectMembership`

`ProjectRole` — это роль, специализация или направление внутри проекта, а не одно свободное место. На одну роль может быть несколько участников. Наличие роли означает, что по ней можно откликаться или приглашать; если роль удалена, новые заявки и приглашения по ней невозможны.

Публичный язык API для RoleInterest:

- `applications` — заявки participant в проект;
- `invitations` — приглашения owner пользователям;
- `notifications` — read-only представление pending RoleInterest.

## 2. Основные сценарии

### Регистрация и авторизация

Пользователь регистрируется через `POST /api/v1/users/`, получает токены через `POST /api/v1/auth/token/login/`, обновляет access-токен через `POST /api/v1/auth/token/refresh/`.

### Создание проекта с ролями

Owner создаёт проект через `POST /api/v1/projects/`. Request body содержит `field_id`, `title`, `description`, `problem`, `image`, `roles`. Вложенный `roles[]` содержит `specialization_id`, `tasks`, `benefits`, `skills`; `skills[]` содержит `skill_id`, `description`, `order`.

### Работа с ролями проекта

Роль можно создать отдельно через `POST /api/v1/project-roles/`, получить через `GET /api/v1/project-roles/` и `GET /api/v1/project-roles/{role_id}/`, обновить через `PATCH /api/v1/project-roles/{role_id}/`, удалить через `DELETE /api/v1/project-roles/{role_id}/`.

Удаление роли запрещено, если по ней есть active `ProjectMembership`, pending application или pending invitation. Если по роли есть только исторические записи — rejected/accepted RoleInterest, left/removed ProjectMembership — они удаляются каскадно вместе с ролью. История по удалённой роли в MVP не сохраняется. `is_open` отсутствует: роль либо существует, либо удалена.

### Отклик на проект

Participant откликается через `POST /api/v1/projects/{project_id}/applications/`. Request body отсутствует. Backend выбирает подходящую `ProjectRole` по специализации текущего пользователя и создаёт `RoleInterest(source = application, status = pending)`.

Owner видит заявки проекта через `GET /api/v1/projects/{project_id}/applications/`.

### Приглашение пользователя

Owner приглашает пользователя через `POST /api/v1/projects/{project_id}/invitations/` с телом `{ "user_id": 2 }`. Backend выбирает подходящую `ProjectRole` по специализации приглашённого пользователя и создаёт `RoleInterest(source = invitation, status = pending)`.

Owner видит исходящие приглашения проекта через `GET /api/v1/projects/{project_id}/invitations/`.

### Принятие и отклонение

`POST /api/v1/role-interests/{interest_id}/accept/` принимает заявку или приглашение. Если `source = application`, действие выполняет owner проекта. Если `source = invitation`, действие выполняет приглашённый пользователь. При accept backend создаёт `ProjectMembership`.

`POST /api/v1/role-interests/{interest_id}/reject/` отклоняет заявку или приглашение. При reject `ProjectMembership` не создаётся.

В MVP нет cancel action, PATCH RoleInterest и статуса `cancelled`.

### Участие в проекте

`ProjectMembership` не создаётся напрямую публичным POST. Оно появляется только при accept RoleInterest. Завершение участия оформлено action endpoints:

- `POST /api/v1/project-memberships/{membership_id}/leave/` — участник покидает проект;
- `POST /api/v1/project-memberships/{membership_id}/remove/` — owner удаляет участника из проекта.

Общий публичный `GET /api/v1/project-memberships/` и технический `PATCH /api/v1/project-memberships/{membership_id}/` отсутствуют.

### Текущий пользователь

`GET /api/v1/users/me/projects/` возвращает объект с `memberships` и pending `invitations`. `GET /api/v1/users/me/applications/` возвращает заявки текущего participant. `GET /api/v1/users/me/notifications/` возвращает pending invitations для participant и pending applications для owner.

## 3. Ключевые сущности API

- **Project:** проект owner с `roles` в detail и `roles_preview` только в списочных карточках.
- **ProjectRole:** роль/направление проекта: `id`, `project_id`, `specialization_id`, `specialization_name`, `tasks`, `benefits`, `skills`, `created_at`, `updated_at`.
- **RoleInterest:** внутренняя модель заявки или приглашения: `source = application|invitation`, `status = pending|accepted|rejected`.
- **ProjectMembership:** участие после accepted RoleInterest: `status = active|left|removed`.
- **Notification:** отдельной модели нет; API возвращает производное read-only представление pending RoleInterest.

## 4. Endpoint reference

### Users and auth

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/users/` | GET | Список пользователей, карточка содержит `specialization_name`, skills с `name`. |
| `/api/v1/users/` | POST | Регистрация пользователя. |
| `/api/v1/users/{user_id}/` | GET | Публичный профиль без `account_type`, с `contacts_visible` и owner-context полями. |
| `/api/v1/users/me/` | GET/PATCH | Профиль текущего пользователя с `account_type`, `notification_enabled`, `owned_project_ids`, без `contacts_visible`. |
| `/api/v1/users/me/avatar/` | PUT/DELETE | Аватар текущего пользователя. |
| `/api/v1/users/set_password/` | POST | Смена пароля текущего пользователя. |
| `/api/v1/auth/token/login/` | POST | JWT login. |
| `/api/v1/auth/token/refresh/` | POST | JWT refresh. |

### Projects and roles

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/projects/` | GET | Список проектов с `roles_preview`. |
| `/api/v1/projects/` | POST | Создать проект с nested `roles`. |
| `/api/v1/projects/{project_id}/` | GET | Детали проекта с `roles` и context fields текущего пользователя. |
| `/api/v1/projects/{project_id}/` | PATCH | Обновить проект. |
| `/api/v1/projects/{project_id}/applications/` | GET/POST | Заявки в проект / откликнуться на проект. |
| `/api/v1/projects/{project_id}/invitations/` | GET/POST | Исходящие приглашения проекта / пригласить пользователя. |
| `/api/v1/project-roles/` | GET/POST | Список и создание ролей. |
| `/api/v1/project-roles/{role_id}/` | GET/PATCH/DELETE | Получение, обновление и удаление роли. |

### Actions

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/role-interests/{interest_id}/accept/` | POST | Принять заявку/приглашение, создать membership. |
| `/api/v1/role-interests/{interest_id}/reject/` | POST | Отклонить заявку/приглашение. |
| `/api/v1/project-memberships/{membership_id}/leave/` | POST | Участник покидает проект. |
| `/api/v1/project-memberships/{membership_id}/remove/` | POST | Owner удаляет участника. |

### Current user resources

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/users/me/projects/` | GET | `{ memberships, invitations }`. |
| `/api/v1/users/me/applications/` | GET | Заявки текущего пользователя. |
| `/api/v1/users/me/notifications/` | GET | Производные уведомления из pending RoleInterest. |
| `/api/v1/users/me/portfolio-works/` | GET/POST | Работы портфолио, включая `image`. |
| `/api/v1/users/me/portfolio-works/{portfolio_work_id}/` | PATCH/DELETE | Управление работой портфолио. |
| `/api/v1/users/me/favorite-projects/` | GET/POST | GET возвращает FavoriteProject с вложенной карточкой проекта; POST возвращает короткую запись избранного. |
| `/api/v1/users/me/favorite-projects/{project_id}/` | DELETE | Удалить проект из избранного. |

## 5. Удалённые из публичного MVP API варианты

- Общий `GET /api/v1/role-interests/` отсутствует.
- `POST /api/v1/project-roles/{role_id}/interests/` заменён на `POST /api/v1/projects/{project_id}/applications/`.
- `POST /api/v1/project-roles/{role_id}/invite/` заменён на `POST /api/v1/projects/{project_id}/invitations/`.
- `GET /api/v1/project-memberships/` отсутствует.
- `PATCH /api/v1/project-memberships/{membership_id}/` отсутствует.
- `GET /api/v1/users/me/incoming-interests/` и `GET /api/v1/users/me/interests/` отсутствуют.
- `cancel` action и статус `cancelled` отсутствуют.

## 6. Правила API

- Action endpoints используются для `accept`, `reject`, `leave`, `remove`.
- Сериализаторы описывают представления и валидацию формы данных; бизнес-решения выполняются в service/view слоях.
- Для пары `(user_id, project_role_id)` существует один RoleInterest.
- Один accepted RoleInterest может породить максимум один ProjectMembership.
- Дублирующее active membership для одного и того же `user/project_role` недопустимо, если этот инвариант закреплён в домене/API.
- Удаление ProjectRole допускает каскадное удаление исторических RoleInterest/ProjectMembership, но только после проверки отсутствия active membership и pending interests.
