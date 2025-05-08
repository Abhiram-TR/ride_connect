# ride_management/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """Custom user model for both admin and regular users"""
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
        ('driver', 'Driver'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
    phone = models.CharField(max_length=15, blank=True)
    
    class Meta:
        db_table = 'users'

class Driver(models.Model):
    """Driver model"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50)
    license_expiry = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_trip', 'On Trip')
    ], default='inactive')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
class Location(models.Model):
    """Popular locations model"""
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_airport = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Vehicle(models.Model):
    """Vehicle model"""
    plate_number = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    color = models.CharField(max_length=30)
    seats = models.IntegerField()
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Maintenance')
    ], default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.model} - {self.plate_number}"

class Trip(models.Model):
    """Trip model"""
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Old text fields (for backward compatibility)
    pickup_location_text = models.CharField(max_length=255, null=True, blank=True)
    dropoff_location_text = models.CharField(max_length=255, null=True, blank=True)
    
    # New location foreign keys
    pickup_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='trips_as_pickup')
    dropoff_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='trips_as_dropoff')
    
    pickup_time = models.DateTimeField()
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    fare = models.DecimalField(max_digits=10, decimal_places=2, default=150.00)  # Fixed fare
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Trip {self.id} - {self.status}"

# Add to models.py

# Add to your models.py file

from django.db import models
from django.contrib.auth.models import AbstractUser
import math

# ... your existing models ...

class DriverLocation(models.Model):
    """Model to store driver's real-time location"""
    driver = models.OneToOneField('Driver', on_delete=models.CASCADE, related_name='location')
    latitude = models.FloatField()
    longitude = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Location for {self.driver.user.first_name} ({self.driver.id})"
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        # Earth's radius in kilometers
        R = 6371
        
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        
        # Haversine formula
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance  # in kilometers