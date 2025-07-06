#!/usr/bin/env python3
"""
Test script for the automatic trip allocation system
Run this after setting up the project to test the Google Maps API integration
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ride_project.settings')
django.setup()

from ride_management.models import Driver, Trip, Location, DriverLocation, CustomUser
from ride_management.services import get_road_distance_google_maps, allocate_trip_to_nearest_driver
from django.utils import timezone
import time

def test_google_maps_api():
    """Test Google Maps Distance Matrix API"""
    print("Testing Google Maps API...")
    
    # Test coordinates (Trivandrum area)
    origin_lat, origin_lng = 8.4834, 76.9198  # Trivandrum
    dest_lat, dest_lng = 8.5241, 76.9366      # Technopark
    
    distance, duration = get_road_distance_google_maps(origin_lat, origin_lng, dest_lat, dest_lng)
    
    if distance is not None:
        print(f"✓ Google Maps API working: {distance:.2f}km, {duration:.1f}min")
        return True
    else:
        print("✗ Google Maps API failed")
        return False

def test_allocation_system():
    """Test the automatic allocation system"""
    print("\nTesting automatic allocation system...")
    
    # Check if we have test data
    drivers = Driver.objects.filter(status='active')
    locations = Location.objects.filter(is_active=True)
    users = CustomUser.objects.filter(user_type='user')
    
    if not drivers.exists():
        print("✗ No active drivers found. Please create test drivers first.")
        return False
    
    if not locations.exists():
        print("✗ No locations found. Please create test locations first.")
        return False
        
    if not users.exists():
        print("✗ No users found. Please create test users first.")
        return False
    
    # Create test driver locations
    for driver in drivers[:3]:  # Test with first 3 drivers
        location, created = DriverLocation.objects.get_or_create(
            driver=driver,
            defaults={
                'latitude': 8.4834 + (driver.id * 0.01),  # Spread drivers around
                'longitude': 76.9198 + (driver.id * 0.01),
                'last_updated': timezone.now()
            }
        )
        if created:
            print(f"✓ Created test location for driver {driver.id}")
    
    # Create a test trip
    pickup_location = locations.first()
    dropoff_location = locations.last()
    test_user = users.first()
    
    # Ensure the pickup location has coordinates
    if not pickup_location.latitude or not pickup_location.longitude:
        print("✗ Pickup location doesn't have coordinates. Please set coordinates for locations.")
        return False
    
    print(f"Creating test trip from {pickup_location.name} to {dropoff_location.name}")
    
    trip = Trip.objects.create(
        user=test_user,
        pickup_location=pickup_location,
        dropoff_location=dropoff_location,
        pickup_time=timezone.now() + timezone.timedelta(minutes=10),
        status='pending'
    )
    
    print(f"✓ Created test trip {trip.id}")
    
    # Test allocation
    print("Testing allocation...")
    success, result = allocate_trip_to_nearest_driver(trip.id)
    
    if success:
        print(f"✓ Trip allocated successfully to driver {result['driver_name']}")
        print(f"  - Distance: {result['distance_km']:.2f}km")
        print(f"  - ETA: {result['estimated_arrival_minutes']}min")
        return True
    else:
        print(f"✗ Allocation failed: {result}")
        return False

def main():
    """Run all tests"""
    print("=== Automatic Trip Allocation Test ===\n")
    
    print(f"Google Maps API Key configured: {'✓' if settings.GOOGLE_MAPS_API_KEY else '✗'}")
    
    if not settings.GOOGLE_MAPS_API_KEY:
        print("✗ Google Maps API key not configured in settings.py")
        return
    
    # Test Google Maps API
    maps_working = test_google_maps_api()
    
    # Test allocation system
    allocation_working = test_allocation_system()
    
    print(f"\n=== Test Results ===")
    print(f"Google Maps API: {'✓' if maps_working else '✗'}")
    print(f"Allocation System: {'✓' if allocation_working else '✗'}")
    
    if maps_working and allocation_working:
        print("\n🎉 All tests passed! Automatic allocation system is working.")
    else:
        print("\n❌ Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()