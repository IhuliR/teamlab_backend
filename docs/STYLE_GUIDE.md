# STYLE_GUIDE.md

Практический гайд по стилю кода для backend TeamLab.

---

## 1. Общие принципы

- Простота важнее гибкости  
- Читаемость важнее “умного кода”  
- Явная логика важнее магии  
- Один источник истины — доменная модель  
- Любая логика должна уважать цепочку:  
  Project → ProjectRole → RoleInterest → ProjectMembership  
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

    def validate(self, data):
        if data['capacity'] < 1:
            raise serializers.ValidationError('capacity must be >= 1')
        return data

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

/project-roles/  
/role-interests/  
/project-memberships/  

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
- side-effects в serializer  
- запросы в цикле  

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
            fields = ('id', 'project_role', 'status')

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
- проверять инварианты  

AI — инструмент, не источник истины.