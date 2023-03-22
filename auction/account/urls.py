import django.urls as dj_urls
from django.contrib.auth import views as auth_views
from . import views

app_name = "account"

urlpatterns = [
    dj_urls.path('', views.dashboard, name='dashboard'),
    dj_urls.path('register/', views.register, name='register'),
    dj_urls.path('edit/', views.edit, name='edit'),
    dj_urls.path('password_change/', auth_views.PasswordChangeView.as_view(
        success_url=dj_urls.reverse_lazy('account:password_change_done')), name='password_change'),
    dj_urls.path('', dj_urls.include('django.contrib.auth.urls')),
]
