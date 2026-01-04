from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('tickets.urls')),
    path('accounts/', include('allauth.urls')),
]
