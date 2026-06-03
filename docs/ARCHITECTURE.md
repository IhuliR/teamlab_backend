# TeamLab Backend Architecture

## 1. Purpose

Backend TeamLab обслуживает MVP workflow командообразования: проекты, роли проекта, заявки/приглашения и участия. OpenAPI schema является главным API-контрактом, Domain Model — главным источником доменной логики.

## 2. Core Architectural Decisions

- `ProjectRole` — направление проекта, а не слот на одного человека.
- На одну роль может быть несколько active participants.
- `is_open` отсутствует: существование роли определяет возможность applications/invitations.
- Context fields не хранятся на ProjectRole. Они возвращаются на project detail и user detail.
- `RoleInterest` остаётся внутренней моделью для applications и invitations.
- `ProjectMembership` создаётся только через accept RoleInterest.
- `leave` и `remove` реализуются action endpoints, а не PATCH status.
- Notifications — read-only представление pending RoleInterest без отдельной модели.
- Удаление ProjectRole блокируется active memberships и pending interests; historical RoleInterest/ProjectMembership удаляются каскадно, история по удалённой роли в MVP не сохраняется.

## 3. MVP Scope

### Входит в MVP

- Users, auth, profile, portfolio works, favorite projects.
- Dictionaries: Field, Specialization, Skill.
- Projects with nested roles creation.
- Project applications and invitations.
- RoleInterest accept/reject actions.
- ProjectMembership leave/remove actions.
- Current user projects, applications and notifications.

### Не входит в MVP

- Notification model/table.
- Invitation model/table.
- IncomingInterest model/table or endpoint as public MVP API.
- Match model/table.
- Public `GET /role-interests/`.
- Public `GET /project-memberships/`.
- `PATCH /project-memberships/{membership_id}/`.
- Cancel action and `cancelled` status.
- Direct public creation of ProjectMembership.

## 4. Backend Responsibility Boundaries

Serializers define API-visible fields and shape validation. Business transitions belong to service/view logic:

- choose matching ProjectRole for application/invitation;
- enforce RoleInterest uniqueness for `(user_id, project_role_id)`;
- accept/reject permissions by RoleInterest source;
- create ProjectMembership during accept;
- prevent ProjectRole deletion when active memberships or pending interests exist;
- cascade-delete historical RoleInterest/ProjectMembership after ProjectRole deletion passes blocking checks;
- compute contacts visibility and context fields.

## 5. Technical Principles

- Use explicit action endpoints for domain transitions.
- Do not expose technical model lists when product flows require applications/invitations/notifications.
- Keep DB schema aligned with API invariants but do not add UI-only tables.
- Keep `contacts_visible` computed, not persisted.
