# ride_management/admin.py
from django.contrib import admin
from .models import CustomUser, Driver, Vehicle, Trip, Location

# Register User model
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'phone', 'user_type']
    list_filter = ['user_type']
    search_fields = ['username', 'first_name', 'last_name', 'email']

# Register Driver model
class DriverAdmin(admin.ModelAdmin):
    list_display = ['get_driver_name', 'license_number', 'license_expiry', 'status']
    list_filter = ['status']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'license_number']
    
    def get_driver_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
    get_driver_name.short_description = 'Driver Name'

# Register Vehicle model
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'model', 'year', 'color', 'seats', 'get_driver', 'status']
    list_filter = ['status', 'year']
    search_fields = ['plate_number', 'model', 'driver__user__first_name', 'driver__user__last_name']
    
    def get_driver(self, obj):
        if obj.driver:
            return f"{obj.driver.user.first_name} {obj.driver.user.last_name}"
        return "Not assigned"
    
    get_driver.short_description = 'Driver'

# Register Location model
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'is_airport', 'is_active', 'latitude', 'longitude']
    list_filter = ['is_airport', 'is_active']
    search_fields = ['name', 'address']

# Register Trip model
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user', 'get_driver', 'get_pickup', 'get_dropoff', 'pickup_time', 'fare', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'driver__user__username', 'pickup_location__name', 'dropoff_location__name']
    
    def get_user(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return "Not assigned"
    
    def get_driver(self, obj):
        if obj.driver:
            return f"{obj.driver.user.first_name} {obj.driver.user.last_name}"
        return "Not assigned"
    
    def get_pickup(self, obj):
        return obj.pickup_location.name if obj.pickup_location else obj.pickup_location_text
    
    def get_dropoff(self, obj):
        return obj.dropoff_location.name if obj.dropoff_location else obj.dropoff_location_text
    
    get_user.short_description = 'User'
    get_driver.short_description = 'Driver'
    get_pickup.short_description = 'Pickup'
    get_dropoff.short_description = 'Dropoff'

# Register models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Driver, DriverAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Trip, TripAdmin)