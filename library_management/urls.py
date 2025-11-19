"""URL configuration for the library_management project."""

from django.contrib import admin
from django.urls import path

urlpatterns = [
	path("admin/", admin.site.urls),
]
