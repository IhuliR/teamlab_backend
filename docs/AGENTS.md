# AGENTS.md

## 1. Типовые риски

**1. Нарушение канонического потока**
Правило: Не создавай ProjectMembership вне цепочки Project → ProjectRole → RoleInterest → accepted  
Как проверить: В diff нет создания membership без ссылки на accepted_interest_id

**2. Слияние стадий RoleInterest и ProjectMembership**
Правило: Не объединяй RoleInterest и ProjectMembership в одну сущность или логику  
Как проверить: Обе модели существуют и используются раздельно

**3. Прямое создание membership**
Правило: Не создавай ProjectMembership без accepted RoleInterest  
Как проверить: В коде нет create() без проверки status=accepted

**4. Дубли RoleInterest**
Правило: Не допускай создание второго RoleInterest для одной пары (user, project_role)  
Как проверить: Есть unique constraint или явная проверка

**5. Игнорирование статусов проекта и роли**
Правило: Не создавай RoleInterest если Project.status != open или ProjectRole.is_open = false  
Как проверить: В логике создания отклика есть проверки статусов

**6. Переполнение capacity**
Правило: Не создавай ProjectMembership если достигнут лимит ProjectRole.capacity  
Как проверить: Перед созданием membership есть проверка количества active

**7. Нарушение логики account_type**
Правило: Не добавляй смену или множественные значения account_type в модели User  
Как проверить: В diff нет изменений поля account_type (тип, количество значений, mutability)

**8. Избранное владельца**
Правило: Не добавляй избранное участников для владельца проекта  
Как проверить: В diff нет моделей и endpoints для такого сценария

**9. Добавление новых сущностей**
Правило: Не добавляй новые модели вне DOMAIN_MODEL.md  
Как проверить: В diff нет новых моделей без ссылки на документ

**10. Расхождение API и домена**
Правило: Не добавляй endpoints, которые создают или изменяют сущности в обход канонического потока  
Как проверить: В diff нет endpoint, создающих ProjectMembership без RoleInterest

**11. Скрытые состояния**
Правило: Не реализуй состояния через флаги или условия вместо явных status-полей  
Как проверить: Нет логики вида “если X и Y, значит статус Z”

**12. Нарушение инвариантов**
Правило: Не изменяй ограничения модели (уникальность, связи, статусы)  
Как проверить: Ограничения из DOMAIN_MODEL.md сохранены без изменений

**13. Нарушение MVP-ограничений (email)**
Правило: Не добавляй email-отправку или внешние уведомления при отсутствии этой функциональности в MVP  
Как проверить: В diff нет SMTP, email-сервисов или внешних интеграций

**14. Нарушение MVP-ограничений (восстановление пароля)**
Правило: Не реализуй восстановление пароля или связанные endpoints  
Как проверить: В diff нет reset-password логики или новых auth endpoints

**15. Invitation как отдельная модель**
Правило: Не создавай Invitation-модель; invite реализуется через RoleInterest.source  
Как проверить: В diff нет модели Invitation, а приглашения используют source=invitation

**16. Notification как отдельная модель**
Правило: Не создавай Notification-модель или отдельный notification API  
Как проверить: Уведомления строятся как UI-представление RoleInterest и ProjectMembership

**17. Раннее открытие контактов**
Правило: Не открывай контакты пользователя без ProjectMembership.status = active  
Как проверить: В ответах API контакты скрыты до активного membership

**18. Invitation не от owner**
Правило: Не создавай invitation, если текущий пользователь не владелец проекта  
Как проверить: В логике invite есть проверка owner проекта

**19. Owner принимает invitation за участника**
Правило: Не позволяй owner принимать или отклонять invitation за участника  
Как проверить: acceptance invitation делает только invited user

**20. Контакты и соцсети**
Правило: Не храни `contacts_visible` в БД; вычисляй его из request.user и active ProjectMembership. `User.social_links` — единое JSONB-поле с ключами `instagram`, `telegram`, `github`, `behance`, `vk`.
Как проверить: В diff нет отдельных telegram/instagram/behance/vk/github полей и нет DB-колонки contacts_visible.

**21. UI-only настройки**
Правило: Не добавляй theme, grid/list view, FAQ accordion, tooltip hints, режимы отображения портфолио/избранного и другие UI-only состояния в API/SQL.
Как проверить: В diff нет новых backend-полей и endpoint под эти элементы.

**22. ProjectRole skills**
Правило: Не добавляй ProjectRoleSkill в MVP. `ProjectRole.key_skills` допустим только как простое JSONB/array-of-strings поле для UI-чипов; не превращай его в связь со Skill без отдельного доменного решения.
Как проверить: В diff нет модели/таблицы/API-схемы ProjectRoleSkill и нет ManyToMany между ProjectRole и Skill.

**23. Match как сущность**
Правило: Не создавай Match-модель; “метч” выводится из ProjectMembership.status = active.
Как проверить: В diff нет модели/таблицы/API endpoint Match.

**24. IncomingInterest как модель**
Правило: Не создавай IncomingInterest-модель. IncomingInterest — только read-only API response/view schema поверх RoleInterest для owner-заявок.
Как проверить: В diff нет модели/таблицы IncomingInterest; endpoint читает RoleInterest с source=application, status=pending и owner-фильтром.

---

## 2. Базовые правила

- Не создавай ProjectMembership без accepted RoleInterest  
- Не создавай RoleInterest при закрытом Project или ProjectRole  
- Не допускай повторный RoleInterest для одной пары user и project_role  
- Не превышай ProjectRole.capacity при создании ProjectMembership  
- Не объединяй RoleInterest и ProjectMembership  
- Не добавляй новые сущности вне DOMAIN_MODEL.md  
- Не добавляй endpoints, которые обходят цепочку Project → ProjectRole → RoleInterest → ProjectMembership  
- Не реализуй состояния вне status-полей моделей  
- Не изменяй инварианты модели без изменения DOMAIN_MODEL.md  
- Не изменяй поле account_type (тип, количество значений, возможность изменения)  
- Не добавляй избранное участников для владельца проекта  
- Не создавай Invitation-модель  
- Не создавай Notification-модель  
- Не создавай Match-модель  
- Не создавай ProjectRoleSkill в MVP  
- Не создавай IncomingInterest-модель  
- Не превращай ProjectRole.key_skills в связь со Skill  
- Не добавляй theme и UI-only состояния в API/SQL  
- Не храни contacts_visible в БД  
- Не открывай contacts без active ProjectMembership  
- Не создавай invitation не от owner  
- Не позволяй owner принимать invitation за участника  


## 3. Запреты

- Запрещено создавать ProjectMembership напрямую, минуя RoleInterest  
- Запрещено изменять каноническую цепочку Project → ProjectRole → RoleInterest → ProjectMembership  
- Запрещено добавлять новые модели без изменения DOMAIN_MODEL.md  
- Запрещено реализовывать скрытые состояния вне явных статусов  
- Запрещено создавать отдельные модели Invitation и Notification  
- Запрещено создавать отдельную модель Match  
- Запрещено создавать ProjectRoleSkill в MVP  
- Запрещено создавать IncomingInterest как модель или таблицу  
- Запрещено хранить contacts_visible и UI-only состояния в SQL  
- Запрещено открывать контакты без active membership  
- Запрещено принимать invitation от имени owner  


## 4. Когда нужно запросить подтверждение

- Изменение структуры или связей моделей  
- Добавление новой сущности или объединение существующих  
- Изменение статусов или жизненного цикла сущностей  
- Изменение API-контрактов, влияющих на основной поток  
