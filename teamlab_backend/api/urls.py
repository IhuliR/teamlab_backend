from django.urls import include, path

from .views import TokenLoginView, TokenRefreshWithUserView


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
    )
]

urlpatterns = [
    path('auth/', include(auth_patterns)),
]
