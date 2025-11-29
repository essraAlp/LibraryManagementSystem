
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from Books import views as book_views
from user import views as user_views
from Barrow import views as borrow_views
from fine import views as fine_views

urlpatterns = [
	path("admin/", admin.site.urls),
	
	# Web pages
	path("", TemplateView.as_view(template_name="index.html"), name="index"),
	path("index.html", TemplateView.as_view(template_name="index.html"), name="index_html"),
	path("profilim.html", TemplateView.as_view(template_name="profilim.html"), name="profile"),
	path("staff_panel.html", TemplateView.as_view(template_name="staff_panel.html"), name="staff_panel"),
	
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
	
	# Staff-only Book Management endpoints
	path("api/staff/books/add/", book_views.add_book, name="staff_add_book"),
	path("api/staff/books/delete/<str:isbn>/", book_views.delete_book, name="staff_delete_book"),
	
	# Staff-only Borrow Management endpoints
	path("api/staff/borrows/create/", borrow_views.create_borrow, name="staff_create_borrow"),
	path("api/staff/borrows/return/<int:borrow_id>/", borrow_views.return_book, name="staff_return_book"),
	path("api/staff/borrows/late/", borrow_views.get_late_borrows, name="staff_late_borrows"),
	path("api/staff/borrows/", borrow_views.get_all_borrows, name="staff_all_borrows"),
	
	# Staff-only Fine Management endpoints
	path("api/staff/fines/", fine_views.get_all_fines, name="staff_all_fines"),
	path("api/staff/fines/pay/<int:fine_id>/", fine_views.mark_fine_paid, name="staff_pay_fine"),
	
	# Staff-only Member Management endpoints
	path("api/staff/members/add/", user_views.add_member, name="staff_add_member"),
	path("api/staff/members/search/", user_views.search_members, name="staff_search_members"),
	path("api/staff/members/delete/<int:user_id>/", user_views.delete_member, name="staff_delete_member"),
	path("api/staff/members/", user_views.get_all_members, name="staff_all_members"),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

