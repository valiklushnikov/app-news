from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from apps.main.models import Post
from permissions import IsAuthorOrReadOnly
from . import models
from . import serializers


class CommentListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_fields = ("post", "author", "parent")
    search_fields = ("content",)
    ordering_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def get_queryset(self):
        return models.Comment.objects.filter(is_active=True).select_related(
            "author", "post", "parent"
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.CommentCreateSerializer
        return serializers.CommentSerializer


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Comment.objects.filter(is_active=True).select_related(
        "author", "post"
    )
    serializer_class = serializers.CommentDetailSerializer
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.CommentUpdateSerializer
        return serializers.CommentDetailSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class MyCommentsView(generics.ListAPIView):
    serializer_class = serializers.CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_fields = ("post", "parent", "is_active")
    search_fields = ("content",)
    ordering_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def get_queryset(self):
        return models.Comment.objects.filter(author=self.request.user).select_related(
            "post", "parent"
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def post_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id, status="published")
    comments = (
        models.Comment.objects.filter(post=post, parent=None, is_active=True)
        .select_related("author")
        .prefetch_related("replies__author")
        .order_by("-created_at")
    )
    serializer = serializers.CommentSerializer(
        comments, many=True, context={"request": request}
    )
    return Response(
        {
            "post": {
                "id": post.id,
                "title": post.title,
                "slug": post.slug,
            },
            "comments": serializer.data,
            "comments_count": post.comments_count,
        }
    )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def comment_replies(request, comment_id):
    parent_comment = get_object_or_404(models.Comment, id=comment_id, is_active=True)
    replies = (
        models.Comment.objects.filter(parent=parent_comment, is_active=True)
        .select_related("author")
        .order_by("created_at")
    )
    serializer = serializers.CommentSerializer(
        replies, many=True, context={"request": request}
    )
    return Response(
        {
            "parent_comment": serializers.CommentSerializer(
                parent_comment, context={"request": request}
            ).data,
            "replies": serializer.data,
            "replies_count": parent_comment.replies_count,
        }
    )
