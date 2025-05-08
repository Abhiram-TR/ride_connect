# ride_management/serializers.py
from rest_framework import serializers
from .models import CustomUser, Driver, Vehicle, Trip, Location

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'user_type']
        extra_kwargs = {'password': {'write_only': True}}

class DriverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Driver
        fields = ['id', 'user', 'license_number', 'license_expiry', 'status']

class VehicleSerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = ['id', 'plate_number', 'model', 'year', 'color', 'seats', 'driver', 'status']

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'latitude', 'longitude', 'is_airport', 'is_active']

class TripSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    driver = DriverSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    pickup_location = LocationSerializer(read_only=True)
    dropoff_location = LocationSerializer(read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'user', 'driver', 'vehicle', 
            'pickup_location', 'dropoff_location',
            'pickup_location_text', 'dropoff_location_text',
            'pickup_time', 'estimated_arrival', 'actual_arrival', 
            'fare', 'status', 'created_at', 'updated_at'
        ]