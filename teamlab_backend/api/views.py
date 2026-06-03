from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
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
    AvatarSerializer,
    CurrentUserDetailSerializer,
    CurrentUserNotificationSerializer,
    CurrentUserUpdateSerializer,
    CurrentUserApplicationCardSerializer,
    CurrentUserMembershipProjectCardSerializer,
    CurrentUserInvitedProjectCardSerializer,
    PortfolioWorkReadSerializer,
    PortfolioWorkWriteSerializer,
    ProjectApplicationCardSerializer,
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
    ProjectRoleReadSerializer,
    ProjectRoleUpdateSerializer,
    ProjectRoleCreateSerializer,
    ProjectInvitationCardSerializer,
    ProjectInvitationCreateSerializer,
    ProjectMembershipActionResultSerializer,
    RoleInterestActionResultSerializer,
    SetPasswordSerializer,
    TokenLoginSerializer,
    TokenRefreshWithUserSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
    FavoriteProjectCreateSerializer,
    FavoriteProjectReadSerializer,
    FieldSerializer,
    SkillSerializer,
    SpecializationSerializer
)
from .filters import (
    ProjectFilter,
    UserFilter
)
from projects.services import (
    accept_role_interest,
    reject_role_interest,
    validate_project_role_can_be_deleted,
    create_project_application,
    create_project_invitation,
    remove_project_membership,
    leave_project_membership
)
from projects.models import (
    Project,
    ProjectRole,
    ProjectMembership,
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
    
    def perform_update(self, serializer):
        project = self.get_object()

        if project.owner_id != self.request.user.id:
            raise PermissionDenied(
                'Редактировать проект может только его владелец.'
            )

        serializer.save()
    
    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        input_serializer.is_valid(raise_exception=True)

        if request.user.account_type != User.AccountType.OWNER:
            raise PermissionDenied(
                'Создавать проекты может только владелец проекта.'
            )

        project = input_serializer.save(owner=request.user)

        output_serializer = ProjectDetailSerializer(
            project,
            context=self.get_serializer_context(),
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

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
            if project.owner_id != request.user.id:
                raise PermissionDenied(
                    'Просматривать заявки и приглашения может '
                    'только владелец проекта.'
                )
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
            if project.owner_id != request.user.id:
                raise PermissionDenied(
                    'Просматривать заявки и приглашения может ' \
                    'только владелец проекта.'
                )
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
                context=self.get_serializer_context(),
            )
            return Response(serializer.data)
        
        input_serializer = ProjectInvitationCreateSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        input_serializer.is_valid(raise_exception=True)

        interest = create_project_invitation(
            project=project,
            actor=request.user,
            invited_user=input_serializer.validated_data['user'],
        )

        serializer = ProjectInvitationCardSerializer(
            interest,
            context=self.get_serializer_context(),
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
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = UserFilter
    search_fields = (
        'username',
        'bio',
        'city',
        'skills__skill__name',
        'specialization__name',
    )
    ordering_fields = ('created_at', 'updated_at', 'username')
    ordering = ('-created_at',)

    def get_queryset(self):
        return User.objects.select_related(
            'specialization',
            'specialization__field',
        ).prefetch_related(
            'skills',
            'skills__skill',
            'portfolio_works',
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        if self.action == 'retrieve':
            return UserDetailSerializer
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'me':
            if self.request.method == 'PATCH':
                return CurrentUserUpdateSerializer
            return CurrentUserDetailSerializer
        if self.action == 'applications':
            return CurrentUserApplicationCardSerializer
        if self.action == 'notifications':
            return CurrentUserNotificationSerializer

        return UserDetailSerializer
    
    def get_permissions(self):
        if self.action in (
            'me',
            'projects',
            'applications',
            'notifications',
        ):
            return (IsAuthenticated(),)
        
        return (AllowAny(),)
    
    @action(detail=False, methods=('get', 'patch'), url_path='me')
    def me(self, request):
        if request.method == 'GET':
            serializer = CurrentUserDetailSerializer(
                request.user,
                context=self.get_serializer_context(),
            )
            return Response(serializer.data)

        serializer = CurrentUserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = CurrentUserDetailSerializer(
            request.user,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data)

    @action(
        detail=False,
        methods=('get',),
        url_path='me/projects',
        permission_classes=(IsAuthenticated,),
    )
    def projects(self, request):
        memberships = ProjectMembership.objects.filter(
            user=request.user,
            status=ProjectMembership.Status.ACTIVE,
        ).select_related(
            'project_role',
            'project_role__project',
            'project_role__specialization',
        ).order_by('-created_at')

        invitations = RoleInterest.objects.filter(
            user=request.user,
            source=RoleInterest.Source.INVITATION,
            status=RoleInterest.Status.PENDING,
        ).select_related(
            'project_role',
            'project_role__project',
            'project_role__specialization',
        ).order_by('-created_at')

        return Response({
            'memberships': CurrentUserMembershipProjectCardSerializer(
                memberships,
                many=True,
                context=self.get_serializer_context(),
            ).data,
            'invitations': CurrentUserInvitedProjectCardSerializer(
                invitations,
                many=True,
                context=self.get_serializer_context(),
            ).data,
        })
    
    @action(
        detail=False,
        methods=('get',),
        url_path='me/applications',
        permission_classes=(IsAuthenticated,),
    )
    def applications(self, request):
        applications = RoleInterest.objects.filter(
            user=request.user,
            source=RoleInterest.Source.APPLICATION,
            status=RoleInterest.Status.PENDING,
        ).select_related(
            'project_role',
            'project_role__project',
            'project_role__specialization',
        ).order_by('-created_at')

        serializer = CurrentUserApplicationCardSerializer(
            applications,
            many=True,
            context=self.get_serializer_context(),
        )

        return Response(serializer.data)

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


class CurrentUserPortfolioWorkDetailView(
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


class CurrentUserAvatarView(generics.GenericAPIView):
    serializer_class = AvatarSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('put', 'delete', 'head', 'options')

    def get_object(self):
        return self.request.user
    
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_object(),
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()

        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save(update_fields=('avatar',))

        return Response(status=status.HTTP_204_NO_CONTENT)
    

class SetPasswordView(generics.GenericAPIView):
    serializer_class = SetPasswordSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('post', 'head', 'options')

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectRoleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = ProjectRole.objects.all()
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    def get_queryset(self):
        return ProjectRole.objects.select_related(
            'project',
            'project__owner',
            'specialization',
        ).prefetch_related(
            'skill_requirements',
            'skill_requirements__skill',
        )

    def get_permissions(self):
        if self.action in ('create', 'partial_update', 'destroy'):
            return (IsAuthenticated(),)

        return (AllowAny(),)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectRoleReadSerializer
        if self.action == 'retrieve':
            return ProjectRoleReadSerializer
        if self.action == 'create':
            return ProjectRoleCreateSerializer
        if self.action in ('partial_update', 'update'):
            return ProjectRoleUpdateSerializer

        return ProjectRoleReadSerializer

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()

        validate_project_role_can_be_deleted(
            project_role=role,
            actor=request.user
        )
        role.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    

class RoleInterestViewSet(viewsets.GenericViewSet):
    queryset = RoleInterest.objects.all()
    serializer_class = RoleInterestActionResultSerializer
    permission_classes = (IsAuthenticated,)
    lookup_url_kwarg = 'interest_id'
    lookup_value_regex = r'\d+'
    http_method_names = ('post', 'head', 'options')

    def get_queryset(self):
        return RoleInterest.objects.select_related(
            'user',
            'project_role',
            'project_role__project',
            'project_role__specialization',
        )
    
    @action(detail=True, methods=('post',), url_path='accept')
    def accept(self, request, interest_id=None):
        interest = accept_role_interest(
            interest=self.get_object(),
            actor=request.user,
        )
        serializer = self.get_serializer(interest)
        return Response(serializer.data)

    @action(detail=True, methods=('post',), url_path='reject')
    def reject(self, request, interest_id=None):
        interest = reject_role_interest(
            interest=self.get_object(),
            actor=request.user,
        )
        serializer = self.get_serializer(interest)
        return Response(serializer.data)


class ProjectMembershipViewSet(viewsets.GenericViewSet):
    queryset = ProjectMembership.objects.all()
    serializer_class = ProjectMembershipActionResultSerializer
    permission_classes = (IsAuthenticated,)
    lookup_url_kwarg = 'membership_id'
    lookup_value_regex = r'\d+'
    http_method_names = ('post', 'head', 'options')

    def get_queryset(self):
        return ProjectMembership.objects.select_related(
            'user',
            'project_role',
            'project_role__project',
            'project_role__specialization',
        )

    @action(detail=True, methods=('post',), url_path='leave')
    def leave(self, request, membership_id=None):
        membership = self.get_object()

        membership = leave_project_membership(
            membership=membership,
            actor=request.user,
        )

        serializer = self.get_serializer(
            membership,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=('post',), url_path='remove')
    def remove(self, request, membership_id=None):
        membership = self.get_object()

        membership = remove_project_membership(
            membership=membership,
            actor=request.user,
        )

        serializer = self.get_serializer(
            membership,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)


class TokenLoginView(TokenObtainPairView):
    serializer_class = TokenLoginSerializer


class TokenRefreshWithUserView(TokenRefreshView):
    serializer_class = TokenRefreshWithUserSerializer
