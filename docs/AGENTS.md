# AGENTS.md

## 1. Типовые риски

**1. Возврат старого RoleInterest list API**

Риск: вернуть общий публичный `GET /role-interests/`.
Правило: публичные списки называются applications, invitations, notifications.

**2. Возврат старого ProjectMembership API**

Риск: вернуть `GET /project-memberships/`, `POST /project-memberships/` или `PATCH /project-memberships/{membership_id}/`.
Правило: ProjectMembership создаётся только через accept RoleInterest, завершается через leave/remove.

**3. Роль как одно место**

Риск: снова считать ProjectRole одним свободным местом.
Правило: ProjectRole — роль/направление; на одну роль может быть несколько участников.

**4. Несколько ролей с одной specialization в проекте**

Риск: разрешить две ProjectRole с одной specialization внутри одного проекта.
Правило: сохранять unique `(project_id, specialization_id)`. Это нужно для однозначного matching role и не ограничивает количество участников на роли.

**5. Дублирующее участие одного пользователя**

Риск: создать дублирующее active membership для одного и того же `user/project_role`, если такой инвариант есть в домене/API.
Правило: проверять user+role, но не запрещать разных пользователей на одной роли.

**6. Повторные applications/invitations**

Риск: создать второй RoleInterest для той же пары `user/project_role` после reject/accept.
Правило: repeated applications/invitations для той же пары не поддерживаются в MVP; unique RoleInterest действует и для pending, и для historical состояний.

**7. Возврат ProjectRole.is_open**

Риск: добавить поле, фильтр или проверку `ProjectRole.is_open`.
Правило: поле удалено из MVP. Роль существует или удалена.

**8. Cancel flow**

Риск: добавить cancel endpoint или статус `cancelled`.
Правило: в MVP заявки и приглашения нельзя отменить.

**9. Новые модели вместо read-only views**

Риск: создать Notification/Invitation/Match/IncomingInterest модель или таблицу.
Правило: applications/invitations — RoleInterest; notifications — read-only представление pending RoleInterest.

**10. Direct membership creation**

Риск: создать ProjectMembership напрямую публичным POST или serializer.save().
Правило: membership создаётся только backend-логикой accept.

**11. PATCH для leave/remove**

Риск: менять статус membership через PATCH.
Правило: использовать action endpoints `leave` и `remove`.

**12. Контекстные поля на роли**

Риск: вернуть `my_*` fields в ProjectRole.
Правило: context fields текущего пользователя живут на project detail и user detail.

**13. Удаление ProjectRole**

Риск: сохранить историю удалённой роли или удалить роль без blocking-проверок.
Правило: роль нельзя удалить при active memberships или pending applications/invitations; historical RoleInterest/ProjectMembership удаляются каскадно, история по удалённой роли в MVP не сохраняется.

**14. Публичное изменение системных справочников**

Риск: вернуть `POST /fields/`, `POST /specializations/` или `POST /skills/`.
Правило: Field, Specialization и Skill управляются через админку/seed/служебные инструменты. Публичный API отдаёт эти справочники только на чтение.

**15. Login по email**

Риск: описать или реализовать login request через email.
Правило: MVP login использует `username + password`; email остаётся контактным/будущим полем.

**16. Смена specialization без проверок**

Риск: позволить participant убрать или изменить specialization при активных связях.
Правило: блокировать смену при active ProjectMembership, pending application или pending invitation. Historical records сами по себе не блокируют.

**17. Account deletion**

Риск: добавить `DELETE /users/me/`.
Правило: account deletion не входит в MVP и требует отдельной бизнес-логики по owned projects, memberships, interests и пользовательским данным.

## 2. Базовые правила

- Не менять backend production-код без явного запроса.
- Не добавлять endpoints, поля и статусы вне OpenAPI-контракта.
- Не создавать Django migrations для документационной SQL-схемы.
- Сверять API-visible поля с `teamlab_api_schema_8.yml`.
- Сверять lifecycle и инварианты с `DOMAIN_MODEL.md`.
- Для поиска использовать контекстные endpoints: `/projects/?search=...` или `/users/?search=...`; глобальный `/search/` не добавлять.

## 3. Запреты

- Не добавлять `is_open`.
- Не добавлять `cancel`/`cancelled`.
- Не создавать Notification/Invitation/IncomingInterest/Match модели.
- Не возвращать публичные общие lists для RoleInterest и ProjectMembership.
- Не создавать ProjectMembership напрямую.
- Не использовать PATCH для leave/remove.
- Не добавлять `POST /fields/` и `POST /specializations/` в публичный MVP API.
- Не добавлять `DELETE /users/me/`.
- Не давать owner управлять `is_featured`/`featured_order` через публичный create/update project API.

## 4. Когда нужно запросить подтверждение

- Если продукт хочет явное ручное указание role_id при application/invitation.
- Если нужно изменить текущие URL или response shape вне OpenAPI.
