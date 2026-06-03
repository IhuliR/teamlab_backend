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
                'Для принудительного запуска используй --force.'
            )

        self.stdout.write('Creating TeamLab demo data...')

        fields = self.create_fields()
        specializations = self.create_specializations(fields)
        skills = self.create_skills()
        users = self.create_users(specializations)
        project = self.create_project(users['owner'], fields['development'])
        roles = self.create_project_roles(project, specializations, skills)

        self.create_user_skills(users, skills)
        interests = self.create_interests_and_memberships(users, roles)
        self.create_favorites(users, project)
        self.create_portfolio_works(users)

        self.stdout.write(self.style.SUCCESS(
            'Demo data created successfully.'
        ))
        self.print_credentials(users, project, roles, interests)

    def create_fields(self):
        development, _ = Field.objects.update_or_create(
            name='Разработка',
            defaults={
                'is_featured': True,
                'featured_order': 1,
            },
        )
        design, _ = Field.objects.update_or_create(
            name='Дизайн',
            defaults={
                'is_featured': True,
                'featured_order': 2,
            },
        )
        ai, _ = Field.objects.update_or_create(
            name='AI',
            defaults={
                'is_featured': True,
                'featured_order': 3,
            },
        )

        return {
            'development': development,
            'design': design,
            'ai': ai,
        }

    def create_specializations(self, fields):
        backend, _ = Specialization.objects.update_or_create(
            name='Backend-разработчик',
            defaults={'field': fields['development']},
        )
        frontend, _ = Specialization.objects.update_or_create(
            name='Frontend-разработчик',
            defaults={'field': fields['development']},
        )
        designer, _ = Specialization.objects.update_or_create(
            name='UI/UX-дизайнер',
            defaults={'field': fields['design']},
        )
        ai_designer, _ = Specialization.objects.update_or_create(
            name='AI-дизайнер',
            defaults={'field': fields['ai']},
        )

        return {
            'backend': backend,
            'frontend': frontend,
            'designer': designer,
            'ai_designer': ai_designer,
        }

    def create_skills(self):
        skill_names = (
            'Python',
            'Django',
            'DRF',
            'PostgreSQL',
            'React',
            'Figma',
            'UX Research',
            'Midjourney',
        )

        result = {}

        for name in skill_names:
            skill, _ = Skill.objects.get_or_create(name=name)
            result[name] = skill

        return result

    def create_users(self, specializations):
        owner = self.create_user(
            username='demo_owner',
            email='owner@example.com',
            account_type=User.AccountType.OWNER,
            specialization=None,
            bio='Owner демо-проекта. Создаёт проекты и собирает команду.',
            city='Москва',
        )
        backend = self.create_user(
            username='demo_backend',
            email='backend@example.com',
            account_type=User.AccountType.PARTICIPANT,
            specialization=specializations['backend'],
            bio='Backend-разработчик. Python, Django, DRF.',
            city='Москва',
        )
        designer = self.create_user(
            username='demo_designer',
            email='designer@example.com',
            account_type=User.AccountType.PARTICIPANT,
            specialization=specializations['designer'],
            bio='UI/UX-дизайнер. Figma, UX Research, продуктовые интерфейсы.',
            city='Санкт-Петербург',
        )
        member = self.create_user(
            username='demo_member',
            email='member@example.com',
            account_type=User.AccountType.PARTICIPANT,
            specialization=specializations['frontend'],
            bio='Frontend-разработчик, уже участвует в демо-проекте.',
            city='Казань',
        )

        return {
            'owner': owner,
            'backend': backend,
            'designer': designer,
            'member': member,
        }

    def create_user(
        self,
        username,
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

    def create_project(self, owner, field):
        project, _ = Project.objects.update_or_create(
            title='Демо-проект TeamLab',
            owner=owner,
            defaults={
                'field': field,
                'description': (
                    'Демо-проект для проверки API, '
                    'Postman и frontend-сценариев.'
                ),
                'problem': (
                    'Нужно собрать команду для разработки MVP платформы '
                    'по поиску проектов и участников.'
                ),
                'status': Project.Status.OPEN,
                'is_featured': True,
                'featured_order': 1,
            },
        )

        return project

    def create_project_roles(self, project, specializations, skills):
        backend_role, _ = ProjectRole.objects.update_or_create(
            project=project,
            specialization=specializations['backend'],
            defaults={
                'tasks': [
                    'Разработать API',
                    'Настроить базу данных',
                    'Подключить авторизацию',
                ],
                'benefits': [
                    'Опыт в командном проекте',
                    'Работа в портфолио',
                ],
            },
        )
        frontend_role, _ = ProjectRole.objects.update_or_create(
            project=project,
            specialization=specializations['frontend'],
            defaults={
                'tasks': [
                    'Собрать интерфейс',
                    'Подключить API',
                ],
                'benefits': [
                    'Практика React',
                    'Портфолио-кейс',
                ],
            },
        )
        designer_role, _ = ProjectRole.objects.update_or_create(
            project=project,
            specialization=specializations['designer'],
            defaults={
                'tasks': [
                    'Собрать UI-kit',
                    'Подготовить макеты экранов',
                ],
                'benefits': [
                    'Кейс в портфолио',
                    'Опыт продуктовой работы',
                ],
            },
        )

        self.add_role_skill(backend_role, skills['Python'], 1)
        self.add_role_skill(backend_role, skills['Django'], 2)
        self.add_role_skill(backend_role, skills['DRF'], 3)
        self.add_role_skill(frontend_role, skills['React'], 1)
        self.add_role_skill(designer_role, skills['Figma'], 1)
        self.add_role_skill(designer_role, skills['UX Research'], 2)

        return {
            'backend': backend_role,
            'frontend': frontend_role,
            'designer': designer_role,
        }

    def add_role_skill(self, project_role, skill, order):
        ProjectRoleSkill.objects.update_or_create(
            project_role=project_role,
            skill=skill,
            defaults={
                'description': f'Нужен навык {skill.name}',
                'order': order,
            },
        )

    def create_user_skills(self, users, skills):
        self.add_user_skill(users['backend'], skills['Python'])
        self.add_user_skill(users['backend'], skills['Django'])
        self.add_user_skill(users['backend'], skills['DRF'])

        self.add_user_skill(users['designer'], skills['Figma'])
        self.add_user_skill(users['designer'], skills['UX Research'])

        self.add_user_skill(users['member'], skills['React'])

    def add_user_skill(self, user, skill):
        UserSkill.objects.get_or_create(
            user=user,
            skill=skill,
        )

    def create_interests_and_memberships(self, users, roles):
        backend_application, _ = RoleInterest.objects.update_or_create(
            user=users['backend'],
            project_role=roles['backend'],
            defaults={
                'source': RoleInterest.Source.APPLICATION,
                'status': RoleInterest.Status.PENDING,
                'reviewed_at': None,
            },
        )

        designer_invitation, _ = RoleInterest.objects.update_or_create(
            user=users['designer'],
            project_role=roles['designer'],
            defaults={
                'source': RoleInterest.Source.INVITATION,
                'status': RoleInterest.Status.PENDING,
                'reviewed_at': None,
            },
        )

        accepted_interest, _ = RoleInterest.objects.update_or_create(
            user=users['member'],
            project_role=roles['frontend'],
            defaults={
                'source': RoleInterest.Source.APPLICATION,
                'status': RoleInterest.Status.ACCEPTED,
                'reviewed_at': timezone.now(),
            },
        )

        membership, _ = ProjectMembership.objects.update_or_create(
            user=users['member'],
            project_role=roles['frontend'],
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

    def print_credentials(self, users, project, roles, interests):
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Demo users:'))
        self.stdout.write(f'owner:    demo_owner / {DEMO_PASSWORD}')
        self.stdout.write(f'backend:  demo_backend / {DEMO_PASSWORD}')
        self.stdout.write(f'designer: demo_designer / {DEMO_PASSWORD}')
        self.stdout.write(f'member:   demo_member / {DEMO_PASSWORD}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Useful demo IDs:'))
        self.stdout.write(f'project_id: {project.id}')
        self.stdout.write(f'backend_role_id: {roles["backend"].id}')
        self.stdout.write(f'frontend_role_id: {roles["frontend"].id}')
        self.stdout.write(f'designer_role_id: {roles["designer"].id}')
        self.stdout.write(
            f'backend_application_interest_id: '
            f'{interests["backend_application"].id}'
        )
        self.stdout.write(
            f'designer_invitation_interest_id: '
            f'{interests["designer_invitation"].id}'
        )
        self.stdout.write(
            f'active_membership_id: {interests["membership"].id}'
        )
