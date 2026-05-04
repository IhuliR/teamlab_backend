# DOMAIN_MODEL.md

## 1. Обзор доменной модели

В системе выделены следующие ключевые сущности:

- User
- Field
- Specialization
- Skill
- UserSkill
- Project
- ProjectRole
- RoleInterest
- ProjectMembership
- PortfolioWork
- FavoriteProject

Центр системы — процесс формирования команды, а не просто проекты.

Основной поток:

Project → ProjectRole → RoleInterest → ProjectMembership

Этот поток определяет:
- как пользователи находят проекты
- как происходит отклик
- как формируется команда

---

## 2. Сущности

### User

**Назначение:**  
Единая сущность пользователя и профиля.

**Ключевые поля:**
- id
- username
- email
- bio
- account_type (`participant` / `owner`)
- specialization_id
- level (`junior` / `middle` / `senior`)
- workload_hours_per_week
- work_format (`remote` / `hybrid`)
- city
- avatar
- created_at
- updated_at

**Связи:**
- User → Project (owner)
- User → UserSkill
- User → RoleInterest
- User → ProjectMembership
- User → PortfolioWork
- User → FavoriteProject
- User → Specialization

**Ограничения:**
- в MVP у пользователя один account_type
- один аккаунт не поддерживает оба сценария одновременно 
- архитектура допускает расширение в будущем
- в MVP у пользователя одна специализация  
- в будущем возможно расширение до нескольких специализаций (через ManyToMany), если появится продуктовая необходимость

---

### Field

**Назначение:**  
Верхнеуровневая категория.

**Ключевые поля:**
- id
- name
- created_at
- updated_at

**Связи:**
- Field → Specialization
- Field → Project

**Ограничения:**
- name уникален

---

### Specialization

**Назначение:**  
Специализация внутри Field.

**Ключевые поля:**
- id
- field_id
- name
- created_at
- updated_at

**Связи:**
- Specialization → Field
- Specialization → User
- Specialization → ProjectRole

**Ограничения:**
- уникальность (field_id, name)

---

### Skill

**Назначение:**  
Справочник навыков.

**Ключевые поля:**
- id
- name
- created_at
- updated_at

**Связи:**
- Skill → UserSkill

**Ограничения:**
- name уникален

---

### UserSkill

**Назначение:**  
Связь пользователя и навыка.

**Ключевые поля:**
- id
- user_id
- skill_id
- level (`basic` / `middle` / `advanced`)
- created_at
- updated_at

**Связи:**
- UserSkill → User
- UserSkill → Skill

**Ограничения:**
- уникальность (user_id, skill_id)

---

### Project

**Назначение:**  
Карточка проекта.

**Ключевые поля:**
- id
- owner_id
- field_id
- title
- description
- idea
- benefits
- status (`open` / `closed`)
- created_at
- updated_at

**Связи:**
- Project → User
- Project → Field
- Project → ProjectRole
- Project → FavoriteProject

**Ограничения:**
- всегда есть owner
- всегда есть field  
- при status = `closed` новые отклики и создание ролей запрещены

---

### ProjectRole

**Назначение:**  
Роль в проекте.

**Ключевые поля:**
- id
- project_id
- specialization_id
- description
- capacity
- is_open
- created_at
- updated_at

**Связи:**
- ProjectRole → Project
- ProjectRole → Specialization
- ProjectRole → RoleInterest
- ProjectRole → ProjectMembership

**Ограничения:**
- capacity >= 1
- при is_open = false новые отклики запрещены  
- роль может быть закрыта независимо от статуса проекта  
- если проект закрыт (`Project.status = closed`), роль считается закрытой независимо от is_open

---

### RoleInterest

**Назначение:**  
Интерес пользователя к роли.

**Ключевые поля:**
- id
- user_id
- project_role_id
- source (`application` / `invitation`)
- status (`pending` / `accepted` / `rejected`)
- reviewed_at
- created_at
- updated_at

**Связи:**
- RoleInterest → User
- RoleInterest → ProjectRole

**Логическая связь:**
- используется для создания ProjectMembership (через accepted_interest_id)

**Source:**
- `application` — пользователь сам откликнулся на роль
- `invitation` — владелец проекта пригласил пользователя на роль

**Решение:**
- `application` принимает или отклоняет владелец проекта
- `invitation` принимает или отклоняет приглашённый пользователь

**Ограничения:**
- уникальность (user_id, project_role_id)  
- для пары (user, project_role) может существовать только один RoleInterest
- `invitation` может создавать только владелец проекта
- interest возможен только если:
  - проект открыт
  - роль открыта

---

### ProjectMembership

**Назначение:**  
Участие в проекте.

**Ключевые поля:**
- id
- user_id
- project_role_id
- accepted_interest_id
- status (`active` / `left` / `removed`)
- joined_at
- ended_at
- created_at
- updated_at

**Связи:**
- ProjectMembership → User
- ProjectMembership → ProjectRole
- ProjectMembership → RoleInterest (через accepted_interest_id)

**Ограничения:**
- создаётся только после accepted RoleInterest  
- accepted_interest_id уникален  
- количество активных участников не превышает capacity  
- проект определяется через project_role (без отдельного FK)
- контакты пользователя доступны только при `ProjectMembership.status = active`

---

### PortfolioWork

**Назначение:**  
Работа пользователя.

**Ключевые поля:**
- id
- user_id
- title
- task
- solution
- image
- technologies
- link
- created_at
- updated_at

**Связи:**
- PortfolioWork → User

**Примечание:**
- в MVP `technologies` хранится как простое поле (строка/список)
- в будущем может быть нормализовано через связь с Skill

---

### FavoriteProject

Избранные проекты участника.

**Ключевые поля:**
- id
- user_id
- project_id
- created_at

**Ограничения:**
- используется только для пользователей с `account_type = participant`
- уникальность (user_id, project_id)

---

## 3. Связи (relations)

- User → Project — OneToMany
- User → UserSkill — OneToMany
- User → RoleInterest — OneToMany
- User → ProjectMembership — OneToMany
- User → PortfolioWork — OneToMany
- User → FavoriteProject — OneToMany

- Field → Specialization — OneToMany
- Field → Project — OneToMany

- Specialization → User — OneToMany
- Specialization → ProjectRole — OneToMany

- User ↔ Skill — ManyToMany через UserSkill

- Project → ProjectRole — OneToMany
- Project → FavoriteProject — OneToMany

- ProjectRole → RoleInterest — OneToMany
- ProjectRole → ProjectMembership — OneToMany

**Важно:**  
Связь RoleInterest → ProjectMembership не является жёсткой OneToOne.  
ProjectMembership ссылается на RoleInterest через accepted_interest_id, но это логическая связь, а не обязательная ORM-конструкция OneToOne.

---

## 4. Жизненный цикл

### Project
- создание: owner создаёт проект
- изменение: редактирует данные
- завершение: статус → closed

### ProjectRole
- создание: добавляется в проект
- изменение: description, capacity, is_open
- завершение: закрытие роли

### RoleInterest
- создание: пользователь откликается (`source = application`) или владелец приглашает (`source = invitation`)
- изменение: смена статуса
- завершение:
  - accepted → membership
  - rejected → завершён

### ProjectMembership
- создание: после accepted
- изменение: статус
- завершение:
  - left / removed

---

## 5. Статусы

### RoleInterest.status
- pending
- accepted
- rejected

### ProjectMembership.status
- active
- left
- removed

### Project.status
- open
- closed

---

## 6. Инварианты

- membership только после accepted interest
- для пары (user, project_role) может существовать только один RoleInterest
- capacity не превышается
- закрытые роли не принимают отклики
- закрытый проект не принимает отклики
- участие нельзя создать напрямую
- UserSkill уникален
- FavoriteProject уникален (user_id, project_id)
- contacts доступны только при active membership

---

## 7. Спорные зоны

- одна или несколько специализаций у пользователя (расширяемо)
- навыки для ролей отсутствуют
- technologies в PortfolioWork не нормализованы
- нет ролей внутри команды
- повторные RoleInterest для одной пары (user, project_role) могут потребоваться в будущем, но в MVP не поддерживаются

---

## 8. Упрощения MVP

- нет email-сервиса
- нет восстановления пароля
- уведомления не являются отдельной бизнес-сущностью; UI строит их как представление данных из RoleInterest и ProjectMembership
- приглашения реализуются через RoleInterest.source, без отдельной Invitation-модели
- нет сложного matching
- нет требований навыков
- нет истории откликов
- повторные RoleInterest для одной пары (user, project_role) не поддерживаются
- нет сложной социальной логики

---

## 9. Принципы модели

- минимализм
- явные состояния
- разделение стадий
- нормализация по необходимости
- без дублирования
- безопасные изменения
- совместимость с Django ORM
