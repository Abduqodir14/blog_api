from rest_framework import generics, permissions, mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from .models import Post, Vote
from .serializers import (
    PostsListSerializer,
    PostSerializer,
    PostDetailSerializer,
    VoteSerializer,
    VotesAnalyticsSerializer,
)


class PostCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostsListView(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostsListSerializer


class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostDetailSerializer


class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        queryset = Post.objects.filter(author=self.request.user)
        return queryset


class VoteCreateView(generics.CreateAPIView, mixins.DestroyModelMixin):
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vote.objects.filter(
            voter=self.request.user, post=Post.objects.get(pk=self.kwargs["pk"])
        )

    def perform_create(self, serializer):
        if self.get_queryset().exists():
            raise ValidationError("You have already voted for this post")
        serializer.save(
            voter=self.request.user, post=Post.objects.get(pk=self.kwargs["pk"])
        )

    def delete(self, request, *args, **kwargs):
        if self.get_queryset().exists():
            self.get_queryset().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ValidationError("You did not voted for this post")


class VotesAnalyticsView(generics.ListAPIView):
    """
    Analytics about how many votes was made. API return analytics aggregated by day.
    """

    queryset = Vote.objects.all()
    serializer_class = VotesAnalyticsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {"created_at": ["gte", "lte"]}

    def get_queryset(self):
        return Vote.objects.all().values("created_at").annotate(votes=Count("post"))
