import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from projects.models import (
    Field,
    Project,
    ProjectMembership,
    ProjectRole,
    ProjectRoleSkill,
    RoleInterest,
    Specialization,
)
from users.models import FavoriteProject, PortfolioWork, Skill, UserSkill


User = get_user_model()

DEMO_PASSWORD = 'DemoPass123!'


class Command(BaseCommand):
    help = 'Create demo data for TeamLab API/Postman/frontend checks.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Allow running seed_demo_data when DEBUG=False.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options['force']:
            raise CommandError(
                'seed_demo_data можно запускать только в DEBUG/dev окружении. '
                'Для принудительного запуска используйте --force.'
            )

        self.stdout.write('Creating TeamLab demo data...')

        file_path = settings.DATA_DIR / 'reference_data.load.json'
        data = self.load_reference_data(file_path)

        fields_by_key = self.create_fields(data['fields'])
        specializations_by_name = self.create_specializations(
            data['specializations'],
            fields_by_key
        )
        skills_by_slug = self.create_skills(data['skills'], fields_by_key)

        users = self.create_users(specializations_by_name)
        projects = self.create_projects(
            users,
            fields_by_key
        )
        roles = self.create_projects_roles(
            projects,
            specializations_by_name,
            skills_by_slug
        )

        self.create_user_skills(users, skills_by_slug)

        interests = self.create_interests_and_memberships(
            users,
            roles
        )

        self.create_favorites(users, projects['demo_project'])
        self.create_portfolio_works(users)

        self.stdout.write(self.style.SUCCESS(
            'Demo data created successfully.'
        ))
        self.print_credentials(users, projects, roles, interests)

    def load_reference_data(self, file_path):
        with open(file_path, encoding='utf-8') as data_file:
            data = json.load(data_file)
        return data

    def create_fields(self, fields_data):
        fields_by_key = {}

        for field_data in fields_data:
            field, _ = Field.objects.update_or_create(
                name=field_data['name'],
                defaults={
                    'is_featured': field_data['is_featured'],
                    'featured_order': field_data['featured_order'],
                }
            )
            fields_by_key[field_data['key']] = field

        return fields_by_key


    def create_specializations(
            self,
            specializations_data,
            fields_by_key
        ):
        specializations_by_name = {}

        for specialization_data in specializations_data:
            specialization, _ = Specialization.objects.update_or_create(
                name=specialization_data['name'],
                defaults={
                    'field': fields_by_key[specialization_data['field']]
                }
            )
            specialization_name = specialization_data['name']
            specializations_by_name[specialization_name] = specialization

        return specializations_by_name

    def create_skills(
            self,
            skills_data,
            fields_by_key,
        ):

        skills_by_slug = {}

        for skill_data in skills_data:
            skill, _ = Skill.objects.update_or_create(
                slug=skill_data['slug'],
                defaults={'name': skill_data['name']},
            )
            field_objects = [
                fields_by_key[field_key]
                for field_key in skill_data['fields']
            ]
            skill.fields.set(field_objects)
            skills_by_slug[skill_data['slug']] = skill

        return skills_by_slug

    def create_user(
        self,
        username,
        display_name,
        email,
        account_type,
        specialization,
        bio,
        city,
    ):
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                'email': email,
                'display_name': display_name,
                'account_type': account_type,
                'specialization': specialization,
                'bio': bio,
                'city': city,
                'is_active': True,
            },
        )

        # Пароль намеренно сбрасывается при каждом запуске,
        # чтобы фронт и Postman всегда имели предсказуемые credentials.
        user.set_password(DEMO_PASSWORD)
        user.save(update_fields=('password',))

        return user

    def create_project(
        self,
        title,
        owner,
        field,
        description,
        problem,
        status,
        is_featured,
        featured_order
    ):
        project, _ = Project.objects.update_or_create(
            title=title,
            owner=owner,
            defaults={
                'field': field,
                'description': description,
                'problem': problem,
                'status': status,
                'is_featured': is_featured,
                'featured_order': featured_order,
            }
        )

        return project

    def add_role_skill(self, project_role, skill, order):
        ProjectRoleSkill.objects.update_or_create(
            project_role=project_role,
            skill=skill,
            defaults={
                'description': f'Нужен навык {skill.name}',
                'order': order,
            },
        )

    def add_user_skill(self, user, skill):
        UserSkill.objects.get_or_create(
            user=user,
            skill=skill,
        )

    def create_users(self, specializations_by_name):
        demo_owner = self.create_user(
            username='demo_owner',
            display_name='Demo Owner',
            email='demo_owner@example.com',
            account_type=User.AccountType.OWNER,
            specialization=None,
            bio='Owner демо-проекта. Создаёт проекты и собирает команду.',
            city='Москва',
        )
        second_project_owner = self.create_user(
            username='second_project_owner',
            display_name='Project Owner',
            email='second_project_owner@example.com',
            account_type=User.AccountType.OWNER,
            specialization=None,
            bio='Owner второго проекта. Создаёт второй проект '
            'и собирает команду. Нужен для дополнительной наглядности',
            city='Санкт-Петербург',
        )
        backend = self.create_user(
            username='demo_backend',
            display_name='Backend Demo',
            email='backend@example.com',
            account_type=User.AccountType.PARTICIPANT,
            specialization=specializations_by_name['Backend-разработчик'],
            bio='Backend-разработчик. Python, Django.',
            city='Москва',
        )
        designer = self.create_user(
            username='demo_designer',
            display_name='Designer Demo',
            email='designer@example.com',
            account_type=User.AccountType.PARTICIPANT,
            specialization=specializations_by_name['UX/UI-дизайнер'],
            bio='UI/UX-дизайнер. Figma, продуктовые интерфейсы.',
            city='Санкт-Петербург',
        )
        member = self.create_user(
            username='demo_member',
            display_name='Member Demo',
            email='member@example.com',
            account_type=User.AccountType.PARTICIPANT,
            specialization=specializations_by_name['Frontend-разработчик'],
            bio='Frontend-разработчик, уже участвует в демо-проекте.',
            city='Казань',
        )

        return {
            'demo_owner': demo_owner,
            'second_project_owner': second_project_owner,
            'backend': backend,
            'designer': designer,
            'member': member,
        }


    def create_projects(self, users, fields_by_key):
        demo_project = self.create_project(
            title='Демо-проект TeamLab',
            owner=users['demo_owner'],
            field=fields_by_key['development'],
            description=(
                'Демо-проект для проверки API, '
                'Postman и frontend-сценариев.'
            ),
            problem=(
                'Нужно собрать команду для разработки MVP платформы '
                'по поиску проектов и участников.'
            ),
            status=Project.Status.OPEN,
            is_featured=True,
            featured_order=1,
        )

        second_project = self.create_project(
            title='Второй проект для сравнения',
            owner=users['second_project_owner'],
            field=fields_by_key['design'],
            description=(
                'Второй проект для фронтенда, '
                'нужен для дополнительного количества.'
            ),
            problem=(
                'Нужно собрать команду для разработки MVP платформы '
                'по поиску проектов и участников.'
            ),
            status=Project.Status.OPEN,
            is_featured=True,
            featured_order=2,
        )


        return {
            'demo_project': demo_project,
            'second_project': second_project
        }

    def create_project_role(
            self,
            project,
            specialization,
            tasks,
            benefits,
    ):
        project_role, _ = ProjectRole.objects.update_or_create(
            project=project,
            specialization=specialization,
            defaults={
                'tasks': tasks,
                'benefits': benefits,
            }
        )
        return project_role

    def create_projects_roles(self, projects, specializations_by_name, skills_by_slug):
        demo_project_backend_role = self.create_project_role(
            project=projects['demo_project'],
            specialization=specializations_by_name['Backend-разработчик'],
            tasks=[
                'Разработать API',
                'Настроить базу данных',
                'Подключить авторизацию',
            ],
            benefits=[
                'Опыт в командном проекте',
                'Работа в портфолио',
            ],
        )
        demo_project_frontend_role = self.create_project_role(
            project=projects['demo_project'],
            specialization=specializations_by_name['Frontend-разработчик'],
            tasks=[
                'Собрать интерфейс',
                'Подключить API',
            ],
            benefits=[
                'Практика React',
                'Портфолио-кейс',
            ],
        )
        demo_project_designer_role = self.create_project_role(
            project=projects['demo_project'],
            specialization=specializations_by_name['UX/UI-дизайнер'],
            tasks=[
                'Собрать UI-kit',
                'Подготовить макеты экранов',
            ],
            benefits=[
                'Кейс в портфолио',
                'Опыт продуктовой работы',
            ],
        )
        second_project_illustrator_role = self.create_project_role(
            project=projects['second_project'],
            specialization=specializations_by_name['Иллюстратор'],
            tasks=[
                'Нарисовать иллюстрации',
                'Кайфовать',
            ],
            benefits=[
                'Практика и кейс',
                'Кайф',
            ],
        )

        self.add_role_skill(
            demo_project_backend_role,
            skills_by_slug['python'],
            1
        )
        self.add_role_skill(
            demo_project_backend_role,
            skills_by_slug['django'],
            2
        )
        self.add_role_skill(
            demo_project_frontend_role,
            skills_by_slug['react'],
            1
        )
        self.add_role_skill(
            demo_project_designer_role,
            skills_by_slug['figma'],
            1
        )
        self.add_role_skill(
            second_project_illustrator_role,
            skills_by_slug['illustration'],
            1
        )

        return {
            'demo_project_backend': demo_project_backend_role,
            'demo_project_frontend': demo_project_frontend_role,
            'demo_project_designer': demo_project_designer_role,
            'second_project_illustrator_role': second_project_illustrator_role
        }

    def create_user_skills(self, users, skills_by_slug):
        self.add_user_skill(users['backend'], skills_by_slug['python'])
        self.add_user_skill(users['backend'], skills_by_slug['django'])
        self.add_user_skill(users['designer'], skills_by_slug['figma'])
        self.add_user_skill(users['member'], skills_by_slug['react'])

    def create_interests_and_memberships(self, users, roles):
        backend_application, _ = RoleInterest.objects.update_or_create(
            user=users['backend'],
            project_role=roles['demo_project_backend'],
            defaults={
                'source': RoleInterest.Source.APPLICATION,
                'status': RoleInterest.Status.PENDING,
                'reviewed_at': None,
            },
        )

        designer_invitation, _ = RoleInterest.objects.update_or_create(
            user=users['designer'],
            project_role=roles['demo_project_designer'],
            defaults={
                'source': RoleInterest.Source.INVITATION,
                'status': RoleInterest.Status.PENDING,
                'reviewed_at': None,
            },
        )

        accepted_interest, _ = RoleInterest.objects.update_or_create(
            user=users['member'],
            project_role=roles['demo_project_frontend'],
            defaults={
                'source': RoleInterest.Source.APPLICATION,
                'status': RoleInterest.Status.ACCEPTED,
                'reviewed_at': timezone.now(),
            },
        )

        membership, _ = ProjectMembership.objects.update_or_create(
            user=users['member'],
            project_role=roles['demo_project_frontend'],
            defaults={
                'role_interest': accepted_interest,
                'status': ProjectMembership.Status.ACTIVE,
                'ended_at': None,
            },
        )

        return {
            'backend_application': backend_application,
            'designer_invitation': designer_invitation,
            'accepted_interest': accepted_interest,
            'membership': membership,
        }

    def create_favorites(self, users, project):
        FavoriteProject.objects.get_or_create(
            user=users['backend'],
            project=project,
        )

    def create_portfolio_works(self, users):
        PortfolioWork.objects.get_or_create(
            user=users['designer'],
            title='Демо UI-kit для TeamLab',
        )

        PortfolioWork.objects.get_or_create(
            user=users['backend'],
            title='Демо API для TeamLab',
        )

    def print_credentials(self, users, projects, roles, interests):
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Demo users:'))
        self.stdout.write(f'demo_owner:    demo_owner / {DEMO_PASSWORD}')
        self.stdout.write(
            f'second_project_owner:    second_project_owner  / {DEMO_PASSWORD}'
        )
        self.stdout.write(f'backend:  demo_backend / {DEMO_PASSWORD}')
        self.stdout.write(f'designer: demo_designer / {DEMO_PASSWORD}')
        self.stdout.write(f'member:   demo_member / {DEMO_PASSWORD}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Useful demo IDs:'))
        self.stdout.write(f"demo_project_id: {projects['demo_project'].id}")
        self.stdout.write(
            f"backend_role_id: {roles['demo_project_backend'].id}"
        )
        self.stdout.write(
            f"frontend_role_id: {roles['demo_project_frontend'].id}"
        )
        self.stdout.write(
            f"designer_role_id: {roles['demo_project_designer'].id}"
        )
        self.stdout.write(
            f"second_project_id: {projects['second_project'].id}"
        )
        self.stdout.write(
            f"illustrator_role_id: "
            f"{roles['second_project_illustrator_role'].id}"
        )
        self.stdout.write(
            f"backend_application_interest_id: "
            f"{interests['backend_application'].id}"
        )
        self.stdout.write(
            f"designer_invitation_interest_id: "
            f"{interests['designer_invitation'].id}"
        )
        self.stdout.write(
            f"active_membership_id: {interests['membership'].id}"
        )
