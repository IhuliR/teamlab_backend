# STYLE_GUIDE.md

## 1. Общие принципы

- OpenAPI contract is the source of truth for public API shape.
- Domain Model is the source of truth for lifecycle and invariants.
- Serializers describe representation and input validation, but do not contain business workflow logic.
- Business actions use explicit action endpoints: `accept`, `reject`, `leave`, `remove`.

## 2. Модели

Do not add MVP-external models:

- Notification;
- Invitation;
- IncomingInterest;
- Match.

Applications and invitations are `RoleInterest` rows. Notifications are read-only API views derived from pending RoleInterest.

## 3. ProjectRole rules

`ProjectRole` means role/specialization/direction inside a project. It is not a single seat. Multiple participants may belong to one role.

Inside one project, one specialization maps to one ProjectRole. Keep unique `(project_id, specialization_id)` in DB/API contracts so matching role selection is deterministic. Do not convert this into a one-participant-per-role rule.

Do not add or validate `ProjectRole.is_open`. The current MVP rule is:

- role exists — applications/invitations may target it;
- role is deleted — new applications/invitations cannot target it;
- deletion is blocked by active memberships or pending interests;
- historical rejected/accepted interests and left/removed memberships are cascade-deleted with the role; history for deleted roles is not preserved in MVP.

## 4. API endpoint style

Use kebab-case and plural collections:

- `/projects/{project_id}/applications/`;
- `/projects/{project_id}/invitations/`;
- `/users/me/notifications/`.

Do not reintroduce old public endpoints:

- `GET /role-interests/`;
- `POST /project-roles/{role_id}/interests/`;
- `POST /project-roles/{role_id}/invite/`;
- `GET /project-memberships/`;
- `PATCH /project-memberships/{membership_id}/`;
- `GET /users/me/incoming-interests/`;
- `GET /users/me/interests/`.
- `POST /fields/`;
- `POST /specializations/`;
- `DELETE /users/me/`.

Public catalogs and authenticated actions:

- public GET: `/projects/`, `/projects/featured/`, `/projects/{project_id}/`, `/users/`, `/users/{user_id}/`, `/fields/`, `/fields/featured/`, `/specializations/`, `/skills/`;
- authenticated write/actions: project create/update, project applications/invitations, `/users/me/`, current-user resources, role-interest accept/reject, membership leave/remove;
- no global `/search/` endpoint in MVP.

## 5. Business actions

Use action endpoints for workflow transitions:

```text
POST /api/v1/role-interests/{interest_id}/accept/
POST /api/v1/role-interests/{interest_id}/reject/
POST /api/v1/project-memberships/{membership_id}/leave/
POST /api/v1/project-memberships/{membership_id}/remove/
```

Do not implement leave/remove as PATCH status. Do not add cancel in MVP.

Do not create repeated applications/invitations for the same user + project_role in MVP. The unique RoleInterest row covers pending and historical states.

Participant specialization updates must be blocked while active ProjectMembership or pending application/invitation exists. Historical accepted/rejected/left/removed records alone do not block the update.

## 6. Serializer guidance

Good serializer responsibilities:

- expose `specialization_name` and skill `name` as read-only fields;
- expose portfolio work `image` wherever portfolio works are returned;
- expose project/user context fields as read-only values computed by view/service layer;
- hide `account_type` from public user detail and keep it in current-user detail.
- keep `is_featured`/`featured_order` out of public create/update serializers; these fields are admin-managed.

Bad serializer responsibilities:

- creating ProjectMembership directly;
- deciding accept/reject permissions;
- performing deletion policy for ProjectRole;
- creating separate notification/invitation objects.

## 7. Examples

Correct action handling shape:

```python
class RoleInterestViewSet(...):
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        result = role_interest_service.accept_interest(
            interest_id=pk,
            actor=request.user,
        )
        return Response(RoleInterestActionSerializer(result).data)
```

Correct membership completion shape:

```python
class ProjectMembershipViewSet(...):
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        membership = membership_service.leave(
            membership_id=pk,
            actor=request.user,
        )
        return Response(ProjectMembershipActionSerializer(membership).data)
```

## 8. AI checklist

Before proposing backend changes, check that the diff does not add removed fields/endpoints, does not create extra models, and does not move business transitions into serializers.
