from django.contrib import admin
from django.urls import path
from vehiclespeed import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This NEW line makes the speed tracker the HOME PAGE
    path('', views.monitor_page, name='home'), 
    
    path('monitor/', views.monitor_page, name='monitor_page'),
    path('live_monitor/', views.live_monitor, name='live_monitor'),
]
