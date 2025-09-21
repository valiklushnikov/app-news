from rest_framework import serializers
from . import models
from apps.main.models import Post


class CommentSerializer(serializers.ModelSerializer):
    author_info = serializers.SerializerMethodField()
    replies_count = serializers.ReadOnlyField()
    is_reply = serializers.ReadOnlyField()

    class Meta:
        model = models.Comment
        fields = (
            "id",
            "content",
            "author",
            "author_info",
            "created_at",
            "updated_at",
            "is_reply",
            "replies_count",
        )
        read_only_fields = ("author", "is_active")

    def get_author_info(self, obj):
        return {
            "id": obj.author.id,
            "username": obj.author.username,
            "full_name": obj.author.full_name,
            "avatar": obj.author.avatar.url if obj.author.avatar else None,
        }


class CommentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Comment
        fields = ("post", "parent", "content")

    def validate_post(self, value):
        if not Post.objects.filter(id=value.id, status="published").exists():
            raise serializers.ValidationError("Post does not exist")
        return value

    def validate_parent(self, value):
        if value:
            post_data = self.initial_data.get("post")
            if post_data:
                if value.post.id != int(post_data):
                    raise serializers.ValidationError(
                        "Parent comment must belong to the same post."
                    )
        return value

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Comment
        fields = ("content",)


class CommentDetailSerializer(CommentSerializer):
    replies = serializers.SerializerMethodField()

    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ("replies",)

    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.filter(is_active=True).order_by("created_at")
            return CommentSerializer(replies, many=True, context=self.context).data
        return []
