# ride_management/api_urls.py (for API endpoints)
from django.urls import path
from . import api_views

urlpatterns = [
    # Authentication
    path('login/', api_views.login, name='api_login'),
    
    # User API
    path('user/active-trip/', api_views.user_active_trip, name='user_active_trip'),
    path('user/nearby-drivers/', api_views.nearby_drivers, name='nearby_drivers'),
    path('user/ride-history/', api_views.user_ride_history, name='user_ride_history'),
    
    # Location API
    path('locations/', api_views.get_locations, name='get_locations'),
    
    # Booking API
    path('book-ride/', api_views.book_ride, name='book_ride'),
    path('cancel-trip/<int:trip_id>/', api_views.cancel_trip, name='cancel_trip'),
    path('trip/<int:trip_id>/auto-assign/', api_views.auto_assign_trip, name='auto_assign_trip'),
    
    # Driver API
    path('driver/status/', api_views.driver_status, name='driver_status'),
    path('driver/toggle-status/', api_views.toggle_driver_status, name='toggle_driver_status'),
    path('driver/active-trip/', api_views.driver_active_trip, name='driver_active_trip'),
    path('driver/stats/', api_views.driver_stats, name='driver_stats'),
    path('driver/pending-requests/', api_views.pending_ride_requests, name='pending_ride_requests'),
    path('driver/trip/<int:trip_id>/accept/', api_views.accept_trip, name='accept_trip'),
    path('driver/trip/<int:trip_id>/start/', api_views.start_trip, name='start_trip'),
    path('driver/trip/<int:trip_id>/complete/', api_views.complete_trip, name='complete_trip'),
    path('driver/vehicle/', api_views.driver_vehicle, name='driver_vehicle'),
    path('driver/trips/', api_views.driver_trip_history, name='driver_trip_history'),
    
    # Driver Location API
    path('driver/update-location/', api_views.update_driver_location, name='update_driver_location'),
    path('driver/update-location/<int:trip_id>/', api_views.update_driver_location, name='update_driver_trip_location'),
    path('driver/location/<int:trip_id>/', api_views.driver_location, name='driver_location'),
    path('admin/api/driver-locations/', api_views.admin_driver_locations, name='admin_driver_locations'),
]