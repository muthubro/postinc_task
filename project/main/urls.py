from django.urls import path

from .views import (
    BrowseView, BookView, AddToFavoritesView, RemoveFromFavoritesView
)

app_name = 'main'

urlpatterns = [
    path('browse/', BrowseView.as_view(), name='browse'),
    path('view/<pk>/', BookView.as_view(), name='view_book'),
    path('add/favorites/<pk>/', AddToFavoritesView.as_view(), name='add_fav'),
    path('remove/favorites/<pk>/', RemoveFromFavoritesView.as_view(), name='remove_fav'),
]