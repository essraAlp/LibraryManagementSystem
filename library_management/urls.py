
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from Books import views as book_views
from user import views as user_views

urlpatterns = [
	path("admin/", admin.site.urls),
	
	# Web pages
	path("", TemplateView.as_view(template_name="index.html"), name="index"),
	path("index.html", TemplateView.as_view(template_name="index.html"), name="index_html"),
	path("profilim.html", TemplateView.as_view(template_name="profilim.html"), name="profile"),
	path("yazarlar.html", TemplateView.as_view(template_name="yazarlar.html"), name="authors"),
	
	# Book endpoints
	path("api/books/search/", book_views.search_books, name="search_books"),
	path("api/books/", book_views.book_list, name="book_list"),
	
	# User authentication endpoints
	path("api/auth/login/", user_views.login_view, name="login"),
	path("api/auth/logout/", user_views.logout_view, name="logout"),
	path("api/auth/session/", user_views.check_session, name="check_session"),
	
	# Member endpoints
	path("api/member/borrowings/", user_views.get_member_borrowings, name="member_borrowings"),
	path("api/member/profile/", user_views.get_member_profile, name="member_profile"),
	path("api/member/profile/update/", user_views.update_member_profile, name="update_profile"),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
