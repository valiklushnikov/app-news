from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from . import models
from . import serializers
from .permissions import IsAuthorOrReadOnly


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "description")
    ordering_fields = ("name", "created_at")
    ordering = ("name",)


class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    lookup_field = "slug"


class PostListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.PostSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_fields = ("category", "author", "status")
    search_fields = ("title", "content")
    ordering_fields = ("created_at", "updated_at", "views_count", "title")
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = models.Post.objects.select_related("author", "category")

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status="published")
        else:
            queryset = queryset.filter(
                Q(author=self.request.user) | Q(status="published")
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.PostCreateUpdateSerializer
        return serializers.PostSerializer


class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Post.objects.select_related("author", "category")
    serializer_class = serializers.PostDetailSerializer
    permissions_classes = (IsAuthorOrReadOnly,)
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.PostCreateUpdateSerializer
        return serializers.PostDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.method == "GET":
            instance.increase_views_count()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MyPostsView(generics.ListAPIView):
    serializer_class = serializers.PostSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_fields = ("category", "author", "status")
    search_fields = ("title", "content")
    ordering_fields = ("created_at", "updated_at", "views_count", "title")
    ordering = ("-created_at",)

    def get_queryset(self):
        return models.Post.objects.filter(author=self.request.user).select_related(
            "author", "category"
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def post_by_category(request, slug):
    category = get_object_or_404(models.Category, slug=slug)
    posts = (
        models.Post.objects.filter(category=category, status="published")
        .select_related("author", "category")
        .order_by("-created_at")
    )
    serializer = serializers.PostSerializer(
        posts, many=True, context={"request": request}
    )
    return Response(
        {
            "category": serializers.CategorySerializer(category).data,
            "posts": serializer.data,
        }
    )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def popular_posts(request):
    posts = (
        models.Post.objects.filter(status="published")
        .select_related("author", "category")
        .order_by("-views_count")[:10]
    )
    serializer = serializers.PostSerializer(
        posts, many=True, context={"request": request}
    )
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def recent_posts(request):
    posts = (
        models.Post.objects.filter(status="published")
        .select_related("author", "category")
        .order_by("-created_at")[:10]
    )
    serializer = serializers.PostSerializer(
        posts, many=True, context={"request": request}
    )
    return Response(serializer.data)
