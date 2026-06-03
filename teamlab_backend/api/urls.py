from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CurrentUserAvatarView,
    CurrentUserFavoriteProjectDeleteView,
    CurrentUserFavoriteProjectListCreateView,
    CurrentUserPortfolioWorkDetailView,
    CurrentUserPortfolioWorkListCreateView,
    FieldListView,
    ProjectMembershipViewSet,
    ProjectRoleViewSet,
    ProjectViewSet,
    RoleInterestViewSet,
    SetPasswordView,
    SkillListCreateView,
    SpecializationListView,
    TokenLoginView,
    TokenRefreshWithUserView,
    UserViewSet,
)


router = DefaultRouter()

router.register(
    'skills',
    SkillListCreateView,
    basename='skills',
)
router.register(
    'fields',
    FieldListView,
    basename='fields',
)
router.register(
    'specializations',
    SpecializationListView,
    basename='specializations',
)
router.register(
    'projects',
    ProjectViewSet,
    basename='projects',
)
router.register(
    'project-roles',
    ProjectRoleViewSet,
    basename='project-roles',
)
router.register(
    'users',
    UserViewSet,
    basename='users',
)
router.register(
    'role-interests',
    RoleInterestViewSet,
    basename='role-interests',
)
router.register(
    'project-memberships',
    ProjectMembershipViewSet,
    basename='project-memberships',
)


auth_patterns = [
    path(
        'token/login/',
        TokenLoginView.as_view(),
        name='token_login',
    ),
    path(
        'token/refresh/',
        TokenRefreshWithUserView.as_view(),
        name='token_refresh',
    ),
]


urlpatterns = [
    path('auth/', include(auth_patterns)),

    path(
        'users/me/avatar/',
        CurrentUserAvatarView.as_view(),
        name='current_user_avatar',
    ),
    path(
        'users/set_password/',
        SetPasswordView.as_view(),
        name='set_password',
    ),
    path(
        'users/me/portfolio-works/',
        CurrentUserPortfolioWorkListCreateView.as_view(),
        name='current_user_portfolio_works',
    ),
    path(
        'users/me/portfolio-works/<int:portfolio_work_id>/',
        CurrentUserPortfolioWorkDetailView.as_view(),
        name='current_user_portfolio_work_detail',
    ),
    path(
        'users/me/favorite-projects/',
        CurrentUserFavoriteProjectListCreateView.as_view(),
        name='current_user_favorite_projects',
    ),
    path(
        'users/me/favorite-projects/<int:project_id>/',
        CurrentUserFavoriteProjectDeleteView.as_view(),
        name='current_user_favorite_project_delete',
    ),

    path('', include(router.urls)),
]
