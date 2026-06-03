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

**4. Дублирующее участие одного пользователя**

Риск: создать дублирующее active membership для одного и того же `user/project_role`, если такой инвариант есть в домене/API.
Правило: проверять user+role, но не запрещать разных пользователей на одной роли.

**5. Возврат ProjectRole.is_open**

Риск: добавить поле, фильтр или проверку `ProjectRole.is_open`.
Правило: поле удалено из MVP. Роль существует или удалена.

**6. Cancel flow**

Риск: добавить cancel endpoint или статус `cancelled`.
Правило: в MVP заявки и приглашения нельзя отменить.

**7. Новые модели вместо read-only views**

Риск: создать Notification/Invitation/Match/IncomingInterest модель или таблицу.
Правило: applications/invitations — RoleInterest; notifications — read-only представление pending RoleInterest.

**8. Direct membership creation**

Риск: создать ProjectMembership напрямую публичным POST или serializer.save().
Правило: membership создаётся только backend-логикой accept.

**9. PATCH для leave/remove**

Риск: менять статус membership через PATCH.
Правило: использовать action endpoints `leave` и `remove`.

**10. Контекстные поля на роли**

Риск: вернуть `my_*` fields в ProjectRole.
Правило: context fields текущего пользователя живут на project detail и user detail.

**11. Удаление ProjectRole**

Риск: сохранить историю удалённой роли или удалить роль без blocking-проверок.
Правило: роль нельзя удалить при active memberships или pending applications/invitations; historical RoleInterest/ProjectMembership удаляются каскадно, история по удалённой роли в MVP не сохраняется.

## 2. Базовые правила

- Не менять backend production-код без явного запроса.
- Не добавлять endpoints, поля и статусы вне OpenAPI-контракта.
- Не создавать Django migrations для документационной SQL-схемы.
- Сверять API-visible поля с `teamlab_api_schema_8.yml`.
- Сверять lifecycle и инварианты с `DOMAIN_MODEL.md`.

## 3. Запреты

- Не добавлять `is_open`.
- Не добавлять `cancel`/`cancelled`.
- Не создавать Notification/Invitation/IncomingInterest/Match модели.
- Не возвращать публичные общие lists для RoleInterest и ProjectMembership.
- Не создавать ProjectMembership напрямую.
- Не использовать PATCH для leave/remove.

## 4. Когда нужно запросить подтверждение

- Если backend должен выбрать одну роль из нескольких ролей с той же специализацией.
- Если продукт хочет явное ручное указание role_id при application/invitation.
- Если нужно изменить текущие URL или response shape вне OpenAPI.
