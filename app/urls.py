from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('reports/', views.reports, name='reports'),
    path('check-in/', views.clock_in_out, name='clock_in_out'),
    path('clock_in/', views.clock_in, name='clock_in'),
    path('clock_out/', views.clock_out, name='clock_out'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('export_csv/', views.export_csv, name='export_csv'),
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='work_hours/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]