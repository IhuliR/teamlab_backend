from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from .serializers import (
    CurrentUserNotificationSerializer,
    CurrentUserApplicationCardSerializer,
    PortfolioWorkReadSerializer,
    PortfolioWorkWriteSerializer,
    ProjectApplicationCardSerializer,
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
    ProjectInvitationCardSerializer,
    ProjectInvitationCreateSerializer,
    TokenLoginSerializer,
    TokenRefreshWithUserSerializer,
    FavoriteProjectCreateSerializer,
    FavoriteProjectReadSerializer,
    FieldSerializer,
    SkillSerializer,
    SpecializationSerializer
)
from .permissions import (
    IsAdminOrReadOnly,
)
from .filters import (
    ProjectFilter
)
from projects.services import (
    validate_project_role_can_be_deleted,
    create_project_application,
    create_project_invitation
)
from projects.models import (
    Project,
    ProjectRole,
    RoleInterest,
    Field,
    Specialization,
)
from users.models import(
    PortfolioWork,
    Skill,
    FavoriteProject,
)


User = get_user_model()


class SkillListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ('name',)
    ordering_fields = ('name', 'created_at')
    ordering = ('name',)


class FieldListView(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    permission_classes = (AllowAny,)
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ('name',)
    ordering_fields = ('name', 'created_at')
    ordering = ('name',)

    @action(detail=False, methods=('get',),url_path='featured')
    def featured(self, request):
        queryset = self.get_queryset().filter(
            is_featured=True,
        ).order_by('featured_order', 'name')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SpecializationListView(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Specialization.objects.select_related('field')
    serializer_class = SpecializationSerializer
    permission_classes = (AllowAny,)
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_fields = ('field_id',)
    search_fields = ('name',)
    ordering_fields = ('name', 'created_at')
    ordering = ('name',)


class ProjectViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    queryset = Project.objects.all()
    http_method_names = ('get', 'post', 'patch', 'head', 'options')

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_fields = ('field_id', 'status')
    filterset_class = ProjectFilter
    search_fields = (
        'title',
        'description',
        'problem',
        'field__name',
        'roles__specialization__name',
        'roles__skill_requirements__skill__name',
    )
    ordering_fields = ('created_at', 'updated_at', 'title')
    ordering = ('-created_at',)

    def get_queryset(self):
        return Project.objects.select_related(
            'owner',
            'field',
        ).prefetch_related(
            'roles',
            'roles__specialization',
            'roles__skill_requirements',
            'roles__skill_requirements__skill',
        ).distinct()

    def get_permissions(self):
        if self.action in (
            'create',
            'partial_update',
            'applications',
            'invitations',
        ):
            return (IsAuthenticated(),)
        
        return (AllowAny(),)

    def get_serializer_class(self):
        if self.action in ('list', 'featured'):
            return ProjectListSerializer
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        if self.action == 'create':
            return ProjectCreateSerializer
        if self.action == 'partial_update':
            return ProjectUpdateSerializer

        return ProjectDetailSerializer

    @action(detail=False, methods=('get',), url_path='featured')
    def featured(self, request):
        queryset = self.get_queryset().filter(
            is_featured=True,
            status=Project.Status.OPEN,
        ).order_by('featured_order', '-created_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=('get', 'post'), url_path='applications')
    def applications(self, request, pk=None):
        project = self.get_object()

        if request.method == 'GET':
            queryset = RoleInterest.objects.filter(
                project_role__project=project,
                source=RoleInterest.Source.APPLICATION,
                status=RoleInterest.Status.PENDING,
            ).select_related(
                'user',
                'user__specialization',
                'project_role',
                'project_role__specialization',
            ).prefetch_related(
                'user__skills',
                'user__skills__skill',
            ).order_by('-created_at')

            serializer = ProjectApplicationCardSerializer(
                queryset,
                many=True,
                context=self.get_serializer_context(),
            )
            return Response(serializer.data)
        
        interest = create_project_application(
            project=project,
            user=request.user,
        )

        serializer = CurrentUserApplicationCardSerializer(
            interest,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    @action(detail=True, methods=('get', 'post'), url_path='invitations')
    def invitations(self, request, pk=None):
        project = self.get_object()

        if request.method == 'GET':
            queryset = RoleInterest.objects.filter(
                project_role__project=project,
                source=RoleInterest.Source.INVITATION,
                status=RoleInterest.Status.PENDING,
            ).select_related(
                'user',
                'project_role',
                'project_role__specialization',
            ).order_by('-created_at')

            serializer = ProjectInvitationCardSerializer(
                queryset,
                many=True,
                conext=self.get_serializer_context(),
            )
            return Response(serializer.data)
        
        input_serializer = ProjectInvitationCreateSerializer(
            data=request.data,
            conext=self.get_serializer_context(),
        )
        input_serializer.is_valid(raise_exception=True)

        interest = create_project_invitation(
            project=project,
            actor=request.user,
            invited_user=input_serializer.validated_data['user'],
        )

        serializer = ProjectInvitationCardSerializer(
            interest,
            conext=self.get_serializer_context(),
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    queryset = User.objects.all()
    http_method_names = ('get', 'post', 'patch', 'head', 'options')
    lookup_value_regex = r'\d+'

    def get_serializer_class(self):
        return super().get_serializer_class()
    
    @action(detail=False, methods=('get', 'patch'), url_path='me')
    def me(self, request):
        ...

    @action(detail=False, methods=('get',), url_path='me/projects')
    def projects(self, request):
        ...
    
    @action(detail=False, methods=('get',), url_path='me/applications')
    def applications(self, request):
        ...

    @action(
        detail=False,
        methods=('get',),
        url_path='me/notifications',
        permission_classes=(IsAuthenticated,),
    )
    def notifications(self, request):
        user = request.user

        if user.account_type == User.AccountType.OWNER:
            queryset = RoleInterest.objects.filter(
                project_role__project__owner=user,
                source=RoleInterest.Source.APPLICATION,
                status=RoleInterest.Status.PENDING,
            )
        else:
            queryset = RoleInterest.objects.filter(
                user=user,
                source=RoleInterest.Source.INVITATION,
                status=RoleInterest.Status.PENDING,
            )

        queryset = queryset.select_related(
            'user',
            'project_role',
            'project_role__project',
            'project_role__specialization',
        ).order_by('-created_at')

        serializer = CurrentUserNotificationSerializer(
            queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
    

class CurrentUserPortfolioWorkListCreateView(
    generics.ListCreateAPIView,
):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return PortfolioWork.objects.filter(
            user=self.request.user,
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PortfolioWorkWriteSerializer
        return PortfolioWorkReadSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CurrentUSerPortfolioWorkDetailView(
    generics.UpdateAPIView,
    generics.DestroyAPIView,
):
    permission_classes = (IsAuthenticated,)
    http_method_names = ('patch', 'delete', 'head', 'options')
    lookup_url_kwarg = 'portfolio_work_id'

    def get_queryset(self):
        return PortfolioWork.objects.filter(
            user=self.request.user,
        )
    
    def get_serializer_class(self):
        return PortfolioWorkWriteSerializer


class CurrentUserFavoriteProjectListCreateView(
    generics.ListCreateAPIView,
):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return FavoriteProject.objects.filter(
            user=self.request.user
        ).select_related('project').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FavoriteProjectCreateSerializer
        return FavoriteProjectReadSerializer
    

class CurrentUserFavoriteProjectDeleteView(
    generics.DestroyAPIView,
):
    permission_classes = (IsAuthenticated,)
    lookup_field = 'project_id'

    def get_queryset(self):
        return FavoriteProject.objects.filter(
            user=self.request.user,
        )
    
    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            project_id=self.kwargs['project_id'],
        )


class CurrentUserAvatarSerializer(
    generics.RetrieveDestroyAPIView
)


class ProjectRoleViewSet(viewsets.ModelViewSet):
    queryset = ProjectRole.objects.all()

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()

        validate_project_role_can_be_deleted(role)
        role.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenLoginView(TokenObtainPairView):
    serializer_class = TokenLoginSerializer


class TokenRefreshWithUserView(TokenRefreshView):
    serializer_class = TokenRefreshWithUserSerializer
