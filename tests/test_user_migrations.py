import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db(transaction=True)
def test_existing_users_are_unverified_after_migration():
    migrate_from = ('users', '0004_skill_fields_skill_slug')
    migrate_to = ('users', '0005_user_is_email_verified')

    executor = MigrationExecutor(connection)
    executor.migrate([migrate_from])
    old_apps = executor.loader.project_state([migrate_from]).apps
    OldUser = old_apps.get_model('users', 'User')
    user = OldUser.objects.create(
        username='existing_user',
        email='existing@example.com',
        password='unusable',
        account_type='owner',
    )

    executor = MigrationExecutor(connection)
    executor.migrate([migrate_to])
    new_apps = executor.loader.project_state([migrate_to]).apps
    NewUser = new_apps.get_model('users', 'User')

    assert NewUser.objects.get(pk=user.pk).is_email_verified is False
