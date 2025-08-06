from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('',auth_views.LoginView.as_view(template_name = 'login.html'),name='login'),
    path('dashboard/',views.Dashboard,name='dashboard'),
    path('logout/',auth_views.LogoutView.as_view(next_page='login'),name='logout'),
    path('deposit/',views.deposit,name='deposit'),
    path('withdraw/',views.withdraw,name='withdraw'),
    path('transfer/',views.transfer,name='transfer'),
    path('history/',views.history,name='history'), 
    path('signup/',views.signup,name='signup'), 

    ]
