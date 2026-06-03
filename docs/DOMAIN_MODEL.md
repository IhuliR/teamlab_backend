# DOMAIN_MODEL.md

## 1. Обзор доменной модели

Каноническая цепочка TeamLab MVP:

`Project -> ProjectRole -> RoleInterest -> ProjectMembership`

`ProjectRole` описывает роль, специализацию или направление в проекте. Это не слот и не одно место для одного участника. На одну роль может быть несколько участников.

Заявки и приглашения не являются отдельными доменными моделями. Они представлены `RoleInterest`:

- `source = application` — participant откликнулся на проект;
- `source = invitation` — owner пригласил пользователя;
- `status = pending|accepted|rejected`.

`ProjectMembership` появляется только после accepted RoleInterest.

## 2. Сущности

### User

Пользователь платформы. `account_type` определяет основной сценарий: `participant` или `owner`. У пользователя может быть `specialization`, набор `UserSkill`, portfolio works, favorite projects и настройка уведомлений `notification_enabled`.

`User.specialization_id` nullable на уровне БД. Через публичный API `participant` без specialization недопустим: при регистрации и обновлении профиля participant обязан иметь `specialization_id`. Для `owner` specialization optional.

Participant не может убрать или изменить `specialization_id`, если у него есть active ProjectMembership, pending RoleInterest(source=application) или pending RoleInterest(source=invitation). Historical records (`rejected`, `accepted`, `left`, `removed`) сами по себе не блокируют смену specialization.

`contacts_visible` не хранится в БД. Это вычисляемое API-поле публичного профиля, доступное в `GET /users/{user_id}/`. В `GET /users/me/` оно не возвращается.

### Field, Specialization, Skill

Справочники. `Specialization` принадлежит `Field`. `Skill` используется в `UserSkill` и `ProjectRoleSkill`.

`Field` и `Specialization` — системные справочники, управляются через админку/seed/служебные инструменты и не создаются пользователем через публичный API. `Field.is_featured` и `Field.featured_order` используются для featured-блока на главной; `featured_order` — внутреннее поле сортировки. "Все профили" не является записью `Field` в базе, это фронтовая синтетическая карточка.

`Skill` — расширяемый пользовательский справочник, поэтому публичный API сохраняет authenticated `POST /skills/`.

### UserSkill

Связь пользователя с навыком и уровнем владения. В API skill item содержит `name` справочного навыка.

### Project

Проект owner. В list/card представлении может возвращать `roles_preview`; в detail возвращает `roles` и context fields текущего пользователя: `matching_role_id`, `matching_role_name`, `my_interest_id`, `my_interest_status`, `my_interest_source`, `my_membership_id`, `my_membership_status`.

`Project.is_featured` и `Project.featured_order` используются для блока "Проекты недели" и управляются администратором через админку/служебные инструменты. Owner проекта не управляет этими полями через публичный create/update API. `featured_order` — внутреннее поле сортировки и не нужно в публичных response schemas.

Для anonymous пользователя project detail возвращает context fields как `null`.

### ProjectRole

Роль, специализация или направление внутри проекта.

Актуальные поля: `project_id`, `specialization_id`, `tasks`, `benefits`, `skills`, timestamps. API также отдаёт `specialization_name`.

В одном проекте не может быть две `ProjectRole` с одной `specialization`: действует уникальность `(project_id, specialization_id)`. Это не означает "одна роль = один участник": одна ProjectRole может иметь сколько угодно active participants.

Удалённое поле `is_open` отсутствует. Роль существует — по ней можно откликаться и приглашать. Роль удалена — по ней нельзя откликаться и приглашать.

Удаление ProjectRole запрещено, если есть:

- active `ProjectMembership`;
- pending `RoleInterest(source = application)`;
- pending `RoleInterest(source = invitation)`.

Роль можно удалить только если нет active ProjectMembership и pending RoleInterest. Historical rejected/accepted RoleInterest и left/removed ProjectMembership по удаляемой роли в MVP удаляются каскадно. История по удалённой роли в MVP не сохраняется.

### ProjectRoleSkill

Нормализованное требование роли к справочному навыку: `skill_id`, `description`, `order`. В API отдаётся `name` навыка.

### RoleInterest

Внутренняя модель для заявок и приглашений. Публичные списочные endpoints используют продуктовые названия `applications`, `invitations`, `notifications`.

Статусы:

- `pending` — ждёт решения;
- `accepted` — принято;
- `rejected` — отклонено.

Статус `cancelled` и cancel flow в MVP отсутствуют.

Инварианты:

- уникальность `(user_id, project_role_id)`;
- repeated applications/invitations для той же пары `(user_id, project_role_id)` не поддерживаются в MVP, включая historical states `accepted` и `rejected`;
- action `accept` может создать ProjectMembership;
- action `reject` не создаёт ProjectMembership.
- если ProjectRole удаляется после прохождения blocking-проверок, исторические RoleInterest этой роли удаляются каскадно.

### ProjectMembership

Факт участия пользователя в проекте по роли. Создаётся backend-логикой только при `POST /role-interests/{interest_id}/accept/`.

Статусы:

- `active` — пользователь участвует;
- `left` — пользователь сам покинул проект;
- `removed` — owner удалил пользователя.

Завершение участия выполняется через `leave` и `remove` action endpoints, а не через PATCH status.

Если ProjectRole удаляется после прохождения blocking-проверок, historical ProjectMembership со статусами `left`/`removed` удаляются каскадно вместе с ролью.

### PortfolioWork

Работа портфолио пользователя. Во всех API-представлениях portfolio work содержит `image`.

### FavoriteProject

Избранный проект participant. `GET /users/me/favorite-projects/` возвращает FavoriteProject и вложенную компактную карточку проекта: `id`, `title`, `image`, `roles_preview`.

## 3. Связи

- `User 1 -> N Project` как owner.
- `Project 1 -> N ProjectRole`.
- `ProjectRole` уникальна внутри проекта по `(project_id, specialization_id)`.
- `ProjectRole 1 -> N ProjectRoleSkill`.
- `User 1 -> N RoleInterest`.
- `ProjectRole 1 -> N RoleInterest`.
- `RoleInterest 0..1 -> 1 ProjectMembership`.
- `ProjectRole 1 -> N ProjectMembership`.
- `User 1 -> N ProjectMembership`.

Нет инварианта “одна роль имеет максимум одного active ProjectMembership”.

## 4. Жизненный цикл

### ProjectRole

Создана -> обновляется -> удаляется, если нет blocking-связей. Отдельного состояния открытости роли нет.

### RoleInterest

`pending -> accepted` или `pending -> rejected`. Принятие создаёт membership; отклонение membership не создаёт.

### ProjectMembership

`active -> left` через leave или `active -> removed` через remove.

## 5. Инварианты

- ProjectRole — не одно место, а направление проекта.
- На одну ProjectRole может быть несколько участников.
- В одном проекте specialization представлена только одной ProjectRole.
- `is_open` отсутствует.
- Удаление ProjectRole запрещено при active memberships или pending interests.
- RoleInterest и ProjectMembership — разные стадии workflow.
- Повторные applications/invitations для той же пары user + project_role не поддерживаются.
- ProjectMembership создаётся только через accept RoleInterest.
- Invitation/Application реализуются через RoleInterest.source.
- История по удалённой ProjectRole в MVP не сохраняется; historical RoleInterest/ProjectMembership удаляются каскадно.
- Notification, Invitation, IncomingInterest и Match не являются моделями MVP.
- Общие публичные списки `GET /role-interests/` и `GET /project-memberships/` отсутствуют.
- Leave/remove реализованы action endpoints.

## 6. Account deletion

Удаление аккаунта не входит в MVP. `DELETE /api/v1/users/me/` не является публичным endpoint текущего API, потому что для удаления нужна отдельная бизнес-логика по owned projects, active memberships, pending interests и пользовательским данным.
