from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('categories/<slug:slug>/', views.CategoryDetailAPIView.as_view(), name='category-detail'),
    path('categories/<slug:slug>/posts/', views.post_by_category, name='post-by-category'),

    path('', views.PostListCreateAPIView.as_view(), name='post-list'),
    path('my-posts/', views.MyPostsView.as_view(), name='my-posts'),
    path('popular/', views.popular_posts, name='popular-posts'),
    path('recent/', views.recent_posts, name='recent-posts'),
    path('<slug:slug>/', views.PostDetailAPIView.as_view(), name='post-detail'),
]