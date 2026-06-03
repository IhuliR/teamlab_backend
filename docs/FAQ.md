# FAQ.md

### Вопрос

Как войти в систему?

### Ответ

Через `POST /api/v1/auth/token/login/` с `username` и `password`. Email нужен при регистрации и хранится как контактное/будущее поле, но в MVP не является login identifier.

### Вопрос

Когда нужен `specialization_id` при регистрации?

### Ответ

`specialization_id` обязателен для `participant` и optional для `owner`. На уровне БД поле nullable, но публичная API-валидация не допускает participant без specialization.

### Вопрос

Можно ли participant поменять specialization?

### Ответ

Можно, если нет active ProjectMembership, pending application или pending invitation. Historical records (`rejected`, `accepted`, `left`, `removed`) сами по себе не блокируют смену specialization.

### Вопрос

Как откликнуться на проект?

### Ответ

Отправить `POST /api/v1/projects/{project_id}/applications/` без request body. Backend определит подходящую ProjectRole по специализации текущего пользователя и создаст `RoleInterest(source = application, status = pending)`.

Если RoleInterest для той же пары `(user, project_role)` уже существует, повторный отклик в MVP не создаётся, включая historical состояния `accepted` и `rejected`.

### Вопрос

Что делает кнопка "Хочу работать" для anonymous пользователя?

### Ответ

Она ведёт пользователя в auth-flow и не вызывает `POST /projects/{project_id}/applications/`. Для anonymous `GET /projects/{project_id}/` возвращает context fields как `null`; после авторизации фронт может заново запросить detail.

### Вопрос

Как owner приглашает участника?

### Ответ

Owner отправляет `POST /api/v1/projects/{project_id}/invitations/` с телом `{ "user_id": 2 }`. Backend определяет подходящую ProjectRole по специализации приглашённого пользователя и создаёт `RoleInterest(source = invitation, status = pending)`.

Если RoleInterest для той же пары `(user, project_role)` уже существует, повторное приглашение в MVP не создаётся, включая historical состояния `accepted` и `rejected`.

### Вопрос

Как owner видит заявки?

### Ответ

Через `GET /api/v1/projects/{project_id}/applications/`. Ответ содержит список RoleInterest application с вложенной карточкой пользователя из user list representation.

### Вопрос

Как participant видит приглашения?

### Ответ

Через `GET /api/v1/users/me/projects/` в массиве `invitations` и через `GET /api/v1/users/me/notifications/`, где pending invitations возвращаются как уведомления.

### Вопрос

Зачем нужны accept/reject?

### Ответ

Это доменные решения по RoleInterest. `accept` переводит RoleInterest в `accepted` и создаёт ProjectMembership. `reject` переводит RoleInterest в `rejected` и не создаёт ProjectMembership.

### Вопрос

Кто может принять или отклонить RoleInterest?

### Ответ

Если `source = application`, решение принимает owner проекта. Если `source = invitation`, решение принимает приглашённый пользователь.

### Вопрос

Почему нет cancel?

### Ответ

В MVP заявки и приглашения нельзя отменять. Поэтому нет cancel endpoint, PATCH RoleInterest и статуса `cancelled`.

### Вопрос

Почему нет Notification-модели, но есть `GET /users/me/notifications/`?

### Ответ

Notifications в MVP — read-only API-представление pending RoleInterest. Для participant это pending invitations, для owner — pending applications на его проекты. Отдельная таблица или модель Notification не создаётся.

### Вопрос

Как понять, что пользователь уже в проекте, без общего `GET /project-memberships/`?

### Ответ

Использовать контекстные поля detail endpoints и current-user resources: `GET /projects/{project_id}/` отдаёт `my_membership_id` и `my_membership_status`, `GET /users/{user_id}/` отдаёт owner-context membership fields, `GET /users/me/projects/` отдаёт memberships текущего пользователя.

### Вопрос

Можно ли создать ProjectMembership напрямую?

### Ответ

Нет. Public `POST /project-memberships/` отсутствует. Membership создаётся только backend-логикой при `POST /role-interests/{interest_id}/accept/`.

### Вопрос

Как участник покидает проект?

### Ответ

Через `POST /api/v1/project-memberships/{membership_id}/leave/`. Request body отсутствует, response возвращает membership action card со статусом `left`.

### Вопрос

Как owner удаляет участника из проекта?

### Ответ

Через `POST /api/v1/project-memberships/{membership_id}/remove/`. Request body отсутствует, response возвращает membership action card со статусом `removed`.

### Вопрос

Что такое ProjectRole теперь?

### Ответ

ProjectRole — роль/специализация/направление внутри проекта. Это не одно место. На одну ProjectRole может быть несколько участников.

В одном проекте не может быть две ProjectRole с одной specialization. Это нужно для однозначного matching role и не означает ограничение "одна роль = один участник".

### Вопрос

Как удалить ProjectRole?

### Ответ

Через `DELETE /api/v1/project-roles/{role_id}/`. Удаление запрещено, если по роли есть active ProjectMembership, pending application или pending invitation. Historical rejected/accepted RoleInterest и left/removed ProjectMembership по удаляемой роли удаляются каскадно; история по удалённой роли в MVP не сохраняется.

### Вопрос

Где хранится contacts_visible?

### Ответ

Нигде. Это вычисляемое API-поле. Оно может возвращаться в публичном профиле `GET /users/{user_id}/`, но не возвращается в `GET /users/me/`.

### Вопрос

Какие справочники можно создавать через публичный API?

### Ответ

`Field` и `Specialization` нельзя создавать через публичный API; ими управляют через админку/seed/служебные инструменты. `Skill` можно создать через authenticated `POST /api/v1/skills/`.

### Вопрос

Что такое featured projects и featured fields?

### Ответ

`GET /api/v1/projects/featured/` отдаёт проекты недели с `is_featured = true`, сортировка `featured_order`, затем `-created_at`. `GET /api/v1/fields/featured/` отдаёт области для главной с сортировкой `featured_order`, затем `name`. Эти поля управляются администратором; `featured_order` не нужен публичному response. "Все профили" — фронтовая синтетическая карточка, не запись `Field`.

### Вопрос

Как работает поиск?

### Ответ

Поиск контекстный: для проектов фронт вызывает `GET /api/v1/projects/?search=...`, для участников — `GET /api/v1/users/?search=...`. Отдельный глобальный `/search/` endpoint не входит в MVP. Multi-value filters `skill_ids` и `specialization_ids` работают как OR внутри группы; разные группы фильтров применяются совместно.

### Вопрос

Можно ли удалить аккаунт?

### Ответ

Нет, account deletion не входит в MVP. `DELETE /api/v1/users/me/` отсутствует, потому что нужен отдельный разбор owned projects, active memberships, pending interests и пользовательских данных.
