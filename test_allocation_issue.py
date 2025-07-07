#!/usr/bin/env python3
"""
Test script to create a scenario that reproduces the allocation issue
"""

import os
import sys
import django

# Add the Django project to the Python path
sys.path.append('/Users/abhiramt/Desktop/work_2/ride_management_project/ride_project')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ride_project.settings')
django.setup()

from ride_management.models import Driver, Trip, DriverLocation, Location, CustomUser
from ride_management.services import find_nearest_driver, haversine_distance
from django.utils import timezone
import logging

# Set up logging to see debug output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_test_scenario():
    """Create a test scenario with multiple drivers at different distances"""
    
    # Create test location for pickup
    pickup_location, _ = Location.objects.get_or_create(
        name="Test Pickup Location",
        defaults={
            'latitude': 8.482959,
            'longitude': 76.916095,
            'address': "Test Pickup Address"
        }
    )
    
    # Create test users and drivers
    test_drivers = []
    driver_locations = [
        (8.483000, 76.916200, "Driver 1 - Very Close"),  # ~50m away
        (8.485000, 76.920000, "Driver 2 - Close"),       # ~500m away  
        (8.490000, 76.930000, "Driver 3 - Medium"),      # ~2km away
        (8.500000, 76.950000, "Driver 4 - Far"),         # ~5km away
    ]
    
    for i, (lat, lng, name) in enumerate(driver_locations, 1):
        # Create user
        user, _ = CustomUser.objects.get_or_create(
            username=f"testdriver{i}",
            defaults={
                'first_name': name,
                'email': f"testdriver{i}@example.com"
            }
        )
        
        # Create driver
        driver, _ = Driver.objects.get_or_create(
            user=user,
            defaults={
                'status': 'active',
                'license_number': f"KL{i:02d}AB{i:04d}",
                'license_expiry': timezone.now().date() + timezone.timedelta(days=365)
            }
        )
        
        # Create driver location
        driver_location, _ = DriverLocation.objects.get_or_create(
            driver=driver,
            defaults={
                'latitude': lat,
                'longitude': lng,
                'last_updated': timezone.now()
            }
        )
        
        # Update if exists
        if not _:
            driver_location.latitude = lat
            driver_location.longitude = lng
            driver_location.last_updated = timezone.now()
            driver_location.save()
        
        # Calculate distance for verification
        distance = haversine_distance(
            pickup_location.latitude, pickup_location.longitude,
            lat, lng
        )
        
        test_drivers.append((driver, distance))
        print(f"Created {name} at distance {distance:.2f}km")
    
    # Create test trip
    customer_user, _ = CustomUser.objects.get_or_create(
        username="testcustomer",
        defaults={
            'first_name': "Test Customer",
            'email': "customer@example.com"
        }
    )
    
    trip, _ = Trip.objects.get_or_create(
        user=customer_user,
        pickup_location=pickup_location,
        dropoff_location=pickup_location,  # Same for simplicity
        defaults={
            'status': 'pending',
            'pickup_time': timezone.now(),
            'fare': 100.0
        }
    )
    
    if not _:
        trip.status = 'pending'
        trip.driver = None
        trip.save()
    
    print(f"\nCreated test trip {trip.id}")
    print(f"Pickup coordinates: {pickup_location.latitude}, {pickup_location.longitude}")
    
    return trip, test_drivers

def test_allocation_logic():
    """Test the allocation logic with our test scenario"""
    
    print("="*60)
    print("CREATING TEST SCENARIO")
    print("="*60)
    
    trip, test_drivers = create_test_scenario()
    
    print("\n" + "="*60)
    print("TESTING ALLOCATION LOGIC")
    print("="*60)
    
    # Test find_nearest_driver
    nearest_driver, result = find_nearest_driver(trip)
    
    if nearest_driver:
        print(f"\n✓ Algorithm selected driver: {nearest_driver.user.first_name}")
        print(f"Distance: {result}km")
        
        # Find the actual closest driver for comparison
        closest_driver, closest_distance = min(test_drivers, key=lambda x: x[1])
        print(f"\n✓ Actual closest driver: {closest_driver.user.first_name}")
        print(f"Distance: {closest_distance:.2f}km")
        
        if nearest_driver.id == closest_driver.id:
            print("\n✅ CORRECT: Algorithm selected the nearest driver!")
        else:
            print("\n❌ ISSUE: Algorithm did NOT select the nearest driver!")
            print("This indicates a bug in the allocation logic.")
    else:
        print(f"\n✗ No driver found: {result}")
        
        # Check why no driver was found
        print("\nDebugging why no driver was found:")
        for driver, distance in test_drivers:
            print(f"Driver {driver.user.first_name}: distance {distance:.2f}km, status {driver.status}")

if __name__ == "__main__":
    test_allocation_logic()