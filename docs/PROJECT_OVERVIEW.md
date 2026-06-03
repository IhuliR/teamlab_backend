# Обзор проекта TeamLab

## TL;DR

TeamLab помогает owner собрать проектную команду, а participant — найти проект и присоединиться к нему. MVP строится вокруг цепочки `Project -> ProjectRole -> RoleInterest -> ProjectMembership`.

`ProjectRole` — направление/роль в проекте, а не одно место. По одной роли может быть несколько участников.

## Основные сценарии использования

### Владелец собирает команду

Owner создаёт проект с nested roles через `POST /api/v1/projects/`, просматривает заявки через `GET /api/v1/projects/{project_id}/applications/`, приглашает пользователя через `POST /api/v1/projects/{project_id}/invitations/`, принимает или отклоняет RoleInterest action endpoints.

### Участник ищет проект и откликается

Participant смотрит список проектов, открывает detail, где видит `roles` и свои context fields, затем отправляет `POST /api/v1/projects/{project_id}/applications/`. Backend выбирает подходящую роль по специализации.

Для anonymous пользователя project detail возвращает `matching_role_id`, `matching_role_name`, `my_interest_id`, `my_interest_status`, `my_interest_source`, `my_membership_id`, `my_membership_status` как `null`. Кнопка "Хочу работать" ведёт anonymous пользователя в auth-flow, а не вызывает application endpoint напрямую.

### Участник работает с приглашениями

Participant видит pending invitations в `GET /api/v1/users/me/projects/` и `GET /api/v1/users/me/notifications/`. Принять/отклонить приглашение можно через `POST /api/v1/role-interests/{interest_id}/accept/` или `/reject/`.

### Пользователь поддерживает профиль

Профиль содержит специализацию, навыки, portfolio works с `image`, настройки видимости, `notification_enabled` и социальные ссылки. `contacts_visible` вычисляется для публичного профиля и не хранится в БД.

Регистрация использует `username`, `email`, `password`, `account_type`; вход выполняется по `username + password`. `specialization_id` обязателен для participant и optional для owner. Participant не может убрать или изменить specialization при active ProjectMembership или pending application/invitation.

Удаление аккаунта не входит в MVP и не представлено endpoint `DELETE /api/v1/users/me/`.

## Типы пользователей

- **owner** создаёт проекты, роли, приглашения, принимает/отклоняет applications, удаляет участников через `remove`.
- **participant** откликается на проекты, принимает/отклоняет invitations, покидает проект через `leave`, ведёт портфолио и избранное.

## Основные сущности

### Project

Проект owner. В списке отдаёт `roles_preview`; в detail отдаёт полный `roles` и context fields текущего пользователя: matching role, interest и membership.

Для главной есть публичный `GET /api/v1/projects/featured/`: проекты с `is_featured = true`, сортировка `featured_order`, затем `-created_at`. `is_featured` и `featured_order` управляются администратором и не редактируются owner через публичный API.

### ProjectRole

Роль/направление внутри проекта. Поле `is_open` удалено из MVP. Роль существует — с ней можно работать; роль удалена — новые applications/invitations невозможны.

В одном проекте specialization представлена только одной ProjectRole. Это не ограничивает количество участников на роли: одна ProjectRole может иметь несколько active participants.

ProjectRole можно удалить только при отсутствии active memberships и pending interests. Historical rejected/accepted interests и left/removed memberships по удаляемой роли в MVP удаляются каскадно. История по удалённой роли не сохраняется.

### RoleInterest

Единая внутренняя модель для applications и invitations. Публичные endpoints используют продуктовые названия:

- `/projects/{project_id}/applications/`;
- `/projects/{project_id}/invitations/`;
- `/users/me/applications/`;
- `/users/me/notifications/`.

Repeated applications/invitations для той же пары `(user_id, project_role_id)` не поддерживаются в MVP. Historical accepted/rejected RoleInterest тоже блокирует создание нового RoleInterest по той же паре.

### ProjectMembership

Факт участия. Создаётся только через accept RoleInterest. Завершение участия выполняется через `leave`/`remove` action endpoints.

### FavoriteProject

Избранный проект participant. List response содержит FavoriteProject и вложенную компактную карточку проекта с `roles_preview`.

## Основные потоки

### Создание проекта и ролей

Owner передаёт nested `roles` в `POST /projects/`. Роли можно добавлять и обновлять отдельно через `/project-roles/`.

### Отклик и приглашение

Applications и invitations создаются на уровне проекта. Backend выбирает подходящую ProjectRole по специализации пользователя.

### Решение по RoleInterest

Accept/reject работают для обоих источников. При application решение принимает owner; при invitation решение принимает приглашённый participant.

### Формирование участия

Accepted RoleInterest создаёт ProjectMembership. Rejected RoleInterest membership не создаёт.

### Мои проекты

`GET /users/me/projects/` возвращает объект:

- `memberships` — активные участия текущего пользователя;
- `invitations` — pending invitations на базе RoleInterest.

## Уведомления

В MVP нет отдельной Notification-модели. `GET /users/me/notifications/` возвращает производное read-only представление pending RoleInterest:

- для participant — pending invitations;
- для owner — pending applications на его проекты.

## Справочники и поиск

`GET /api/v1/fields/`, `GET /api/v1/specializations/`, `GET /api/v1/skills/` публичны. `Field` и `Specialization` управляются администратором/seed/служебными инструментами; публичных create endpoints для них нет. `Skill` можно создавать авторизованному пользователю через `POST /api/v1/skills/`.

`GET /api/v1/fields/featured/` возвращает featured области для главной. "Все профили" — фронтовая синтетическая карточка, а не запись `Field`.

Поиск в MVP контекстный: раздел проектов использует `GET /api/v1/projects/?search=...`, раздел участников использует `GET /api/v1/users/?search=...`. Отдельный глобальный `/search/` endpoint не добавляется.

## Ключевые инварианты домена

- ProjectRole не является одним местом.
- На одну ProjectRole может быть несколько участников.
- В одном проекте нет двух ProjectRole с одной specialization.
- `is_open` отсутствует.
- RoleInterest уникален для пары `(user_id, project_role_id)`.
- Повторные applications/invitations для той же пары user + project_role не поддерживаются.
- Один accepted RoleInterest может породить максимум один ProjectMembership.
- ProjectMembership не создаётся напрямую публичным API.
- Historical rejected/accepted interests и left/removed memberships по удаляемой ProjectRole в MVP удаляются каскадно.
- Cancel flow и статус `cancelled` не входят в MVP.
- Notification, Invitation, IncomingInterest и Match не являются моделями MVP.
