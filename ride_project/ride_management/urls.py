# Update this section in your ride_management/urls.py file

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth URLs
    path('', auth_views.LoginView.as_view(template_name='admin/login1.html'), name='login'),
    path('logout/', views.admin_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Drivers
    path('drivers/', views.drivers_list, name='drivers_list'),
    path('drivers/add/', views.add_driver, name='add_driver'),
    path('drivers/edit/<int:driver_id>/', views.edit_driver, name='edit_driver'),
    
    # Vehicles
    path('vehicles/', views.vehicles_list, name='vehicles_list'),
    path('vehicles/add/', views.add_vehicle, name='add_vehicle'),
    path('vehicles/edit/<int:vehicle_id>/', views.edit_vehicle, name='edit_vehicle'),
    
    # Trips
    path('trips/', views.trips_list, name='trips_list'),
    path('trips/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    
    # Users
    path('users/', views.users_list, name='users_list'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    
    # Locations
    path('locations/', views.locations_list, name='locations_list'),
    path('locations/add/', views.add_location, name='add_location'),
    path('locations/edit/<int:location_id>/', views.edit_location, name='edit_location'),
    
    # Add the driver tracking URL here
    path('driver-tracking/', views.driver_tracking, name='driver_tracking'),
]