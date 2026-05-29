# STYLE_GUIDE.md

Практический гайд по стилю кода для backend TeamLab.

---

## 1. Общие принципы

- Простота важнее гибкости  
- Читаемость важнее “умного кода”  
- Явная логика важнее магии  
- DOMAIN_MODEL.md — источник истины для доменной логики, lifecycle и инвариантов
- OpenAPI/API-контракт — источник истины для endpoints, request/response schemas и API-visible полей
- Любая логика должна уважать цепочку:  
  Project → ProjectRole → RoleInterest → ProjectMembership  
- Не создавать сущности под UI-представления, например под уведомления  
- Invitation реализуется через RoleInterest.source  
- Match не является моделью; состояние совпадения выводится из active ProjectMembership
- IncomingInterest не является моделью; это read-only API response/view поверх RoleInterest для owner-заявок
- ProjectRoleSkill входит в MVP и описывает требования роли к справочным Skill
- contacts_visible не хранится в БД, а вычисляется для API-ответа
- соцсети пользователя хранятся единым `User.social_links`, без отдельных backend-полей под конкретные соцсети
- light/dark theme и прочие UI-only режимы не добавляются в API/SQL
- Соблюдай существующий стиль проекта  

---

## 2. Форматирование кода

- Отступы: 4 пробела  
- Табы запрещены  
- Кавычки: одинарные '  
- Следовать PEP 8  
- Максимальная длина строки: 88–100 символов  

Пустые строки:
- между классами — 2  
- между методами — 1  

Если PEP 8 конфликтует с правилами проекта — приоритет у проекта

---

## 3. Структура проекта

app/
 ├── models.py
 ├── serializers.py
 ├── views.py
 ├── permissions.py
 ├── services.py (если нужен)
 ├── filters.py (если есть фильтрация)

Правила:

- models — только данные и простая логика  
- serializers — только валидация и преобразование  
- views — только orchestration  
- permissions — только доступ  
- services — бизнес-логика (если нужна)  

Запрещено:

- смешивать слои  
- переносить логику между слоями  

---

## 4. Модели (Models)

Нейминг:

- модели: PascalCase → ProjectRole  
- поля: snake_case → project_role_id  

Связи (пример):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='roles'
    )

Статусы (пример):

    status = models.CharField(choices=StatusChoices)

Запрещено:
- вычислять статус через if-условия

Ограничения (пример):

    class RoleInterest(models.Model):
        class Meta:
            constraints = [
                models.UniqueConstraint(
                    fields=['user', 'project_role'],
                    name='unique_user_role_interest'
                )
            ]

---

## 5. Сериализаторы

Разделение:

- ReadSerializer  
- WriteSerializer  

Пример:

    class ProjectReadSerializer(serializers.ModelSerializer):
        owner = UserShortSerializer()

    class ProjectWriteSerializer(serializers.ModelSerializer):
        class Meta:
            fields = ('title', 'description')

Валидация:

    def validate_tasks(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('tasks must be a list')
        return value

Запрещено:

- бизнес-логика  
- side-effects  

---

## 6. ViewSet / API слой

- использовать ModelViewSet  
- queryset обязателен  

Пример:

    def get_serializer_class(self):
        if self.action in ('create', 'update'):
            return ProjectWriteSerializer
        return ProjectReadSerializer

@action использовать только если это не CRUD:

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        ...

---

## 7. Permissions

Пример:

    class IsOwner(permissions.BasePermission):
        def has_object_permission(self, request, view, obj):
            return obj.owner == request.user

Правила:

- логика доступа только в permissions  
- не писать её во view  

---

## 8. Бизнес-логика (КРИТИЧНО)

Запрещено:

- во view  
- в serializer  

Разрешено:

- model methods  
- services  

Плохо:

    def perform_create(self, serializer):
        ProjectMembership.objects.create(...)

Хорошо:

    class RoleInterest(models.Model):
        def accept(self):
            if self.status != 'pending':
                raise ValueError('Invalid state')

            self.status = 'accepted'
            self.save()

            ProjectMembership.objects.create(
                user=self.user,
                project_role=self.project_role,
                accepted_interest=self
            )

---

## 9. Работа с QuerySet

Обязательно:

    select_related('project')
    prefetch_related('roles')

Запрещено:

- запросы в цикле  

---

## 10. Ошибки и ответы

Формат:

    {
      "detail": "error message"
    }

или

    {
      "field": ["error message"]
    }

HTTP-коды:

- 200 — OK  
- 201 — created  
- 204 — deleted  
- 400 — validation error  
- 401 — unauthorized  
- 403 — forbidden  
- 404 — not found  
- 409 — conflict  

---

## 11. Нейминг

- переменные — snake_case  
- классы — PascalCase  
- константы — UPPER_CASE  
- endpoints — kebab-case  

Примеры:

/api/v1/project-roles/
/api/v1/role-interests/
/api/v1/project-memberships/

---

## 12. Запрещённые практики

- бизнес-логика во view  
- бизнес-логика в serializer  
- создание ProjectMembership напрямую  
- объединение RoleInterest и ProjectMembership  
- обход доменной цепочки  
- “магические” флаги вместо status  
- дублирование логики  
- изменение account_type  
- новые модели вне DOMAIN_MODEL.md  
- модели Invitation и Notification  
- модели Match
- модели IncomingInterest
- legacy JSON-поле навыков роли
- избранное участников для владельца проекта  
- theme, grid/list view, tooltip hints и другие UI-only состояния
- отдельные поля соцсетей вместо `social_links`
- сущности только для UI-представлений  
- side-effects в serializer  
- запросы в цикле  
- owner принимает invitation за участника

---

## 13. Примеры кода

Корректный ViewSet:

    class ProjectViewSet(viewsets.ModelViewSet):
        queryset = Project.objects.all()

        def get_serializer_class(self):
            if self.action in ('create', 'update'):
                return ProjectWriteSerializer
            return ProjectReadSerializer

Корректный serializer:

    class RoleInterestSerializer(serializers.ModelSerializer):
        class Meta:
            model = RoleInterest
            fields = ('id', 'project_role', 'source', 'status')

        def validate(self, data):
            if not data['project_role'].is_open:
                raise serializers.ValidationError('Role is closed')
            return data

Плохая практика:

    def create(self, validated_data):
        interest = RoleInterest.objects.create(**validated_data)
        ProjectMembership.objects.create(...)
        return interest

Исправленный вариант:

    def create(self, validated_data):
        return RoleInterest.objects.create(**validated_data)

---

## 14. Работа с AI

- учитывать AGENTS.md  
- проверять код после генерации  
- не добавлять новые сущности  
- не добавлять Invitation и Notification как модели  
- не добавлять Match как модель MVP
- не добавлять IncomingInterest как модель  
- не возвращать legacy JSON-поле навыков роли вместо ProjectRoleSkill
- не добавлять избранное участников для владельца проекта  
- не хранить contacts_visible или UI-only состояния в SQL  
- проверять инварианты  

AI — инструмент, не источник истины.
