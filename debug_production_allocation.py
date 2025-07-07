#!/usr/bin/env python3
"""
Debug script to check the real production allocation state
"""

import os
import sys
import django

# Add the Django project to the Python path
sys.path.append('/Users/abhiramt/Desktop/work_2/ride_management_project/ride_project')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ride_project.settings')
django.setup()

from ride_management.models import Driver, Trip, DriverLocation, Location
from ride_management.services import find_nearest_driver
from django.utils import timezone
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_system_state():
    """Check the current state of the system"""
    
    print("=" * 60)
    print("SYSTEM STATE ANALYSIS")
    print("=" * 60)
    
    # Check drivers
    all_drivers = Driver.objects.all()
    active_drivers = Driver.objects.filter(status='active')
    
    print(f"Total drivers: {all_drivers.count()}")
    print(f"Active drivers: {active_drivers.count()}")
    
    print("\nDriver details:")
    for driver in all_drivers:
        print(f"  Driver {driver.id}: {driver.user.first_name} {driver.user.last_name}")
        print(f"    Status: {driver.status}")
        print(f"    Created: {driver.created_at}")
        
        # Check driver location
        try:
            location = driver.location
            if location:
                print(f"    Location: {location.latitude}, {location.longitude}")
                print(f"    Last updated: {location.last_updated}")
                
                # Check if location is recent (within 5 minutes)
                time_threshold = timezone.now() - timezone.timedelta(minutes=5)
                is_recent = location.last_updated > time_threshold
                print(f"    Recent location: {'Yes' if is_recent else 'No'}")
            else:
                print("    Location: No location data")
        except Exception as e:
            print(f"    Location: Error - {e}")
        
        # Check if driver has active trips
        active_trips = Trip.objects.filter(
            driver=driver,
            status__in=['accepted', 'in_progress', 'arrived']
        )
        print(f"    Active trips: {active_trips.count()}")
        print()
    
    # Check trips
    all_trips = Trip.objects.all()
    pending_trips = Trip.objects.filter(status='pending')
    
    print(f"Total trips: {all_trips.count()}")
    print(f"Pending trips: {pending_trips.count()}")
    
    print("\nTrip details:")
    for trip in all_trips.order_by('-created_at')[:5]:  # Show latest 5 trips
        print(f"  Trip {trip.id}: {trip.status}")
        print(f"    User: {trip.user.first_name if trip.user else 'None'}")
        print(f"    Pickup: {trip.pickup_location}")
        print(f"    Driver: {trip.driver.user.first_name if trip.driver else 'None'}")
        print(f"    Created: {trip.created_at}")
        print()
    
    # Check locations
    locations = Location.objects.all()
    print(f"Total locations: {locations.count()}")
    
    print("\nLocation details:")
    for location in locations:
        print(f"  {location.name}: {location.latitude}, {location.longitude}")
    
    return pending_trips

def test_allocation_with_real_data():
    """Test allocation with real production data"""
    
    print("\n" + "=" * 60)
    print("TESTING ALLOCATION WITH REAL DATA")
    print("=" * 60)
    
    pending_trips = Trip.objects.filter(status='pending')
    
    if not pending_trips.exists():
        print("No pending trips found. Creating a test trip...")
        
        # Get a location to use
        location = Location.objects.first()
        if not location:
            print("No locations found. Cannot create test trip.")
            return
        
        # Get a user
        from ride_management.models import CustomUser
        user = CustomUser.objects.first()
        if not user:
            print("No users found. Cannot create test trip.")
            return
        
        # Create test trip
        test_trip = Trip.objects.create(
            user=user,
            pickup_location=location,
            dropoff_location=location,
            pickup_time=timezone.now(),
            status='pending'
        )
        print(f"Created test trip {test_trip.id}")
        pending_trips = [test_trip]
    
    # Test allocation for each pending trip
    for trip in pending_trips:
        print(f"\nTesting allocation for trip {trip.id}:")
        print(f"  Pickup: {trip.pickup_location}")
        if trip.pickup_location:
            print(f"  Coordinates: {trip.pickup_location.latitude}, {trip.pickup_location.longitude}")
        
        # Test with debug enabled
        nearest_driver, result = find_nearest_driver(trip, debug=True)
        
        if nearest_driver:
            print(f"  ✓ Found driver: {nearest_driver.user.first_name} {nearest_driver.user.last_name}")
            print(f"  Distance: {result}km")
        else:
            print(f"  ✗ No driver found: {result}")
            
            # Analyze why no driver was found
            print("\n  Analyzing why no driver was found:")
            
            # Check active drivers
            active_drivers = Driver.objects.filter(status='active')
            print(f"    Active drivers: {active_drivers.count()}")
            
            # Check drivers with recent locations
            time_threshold = timezone.now() - timezone.timedelta(minutes=5)
            drivers_with_recent_locations = Driver.objects.filter(
                status='active',
                location__last_updated__gt=time_threshold
            )
            print(f"    Drivers with recent locations: {drivers_with_recent_locations.count()}")
            
            # Check drivers without active trips
            drivers_without_trips = []
            for driver in active_drivers:
                active_trip_exists = Trip.objects.filter(
                    driver=driver,
                    status__in=['accepted', 'in_progress', 'arrived']
                ).exists()
                if not active_trip_exists:
                    drivers_without_trips.append(driver)
            
            print(f"    Drivers without active trips: {len(drivers_without_trips)}")
            
            if drivers_without_trips:
                print("    Available drivers:")
                for driver in drivers_without_trips:
                    try:
                        location = driver.location
                        if location:
                            print(f"      {driver.user.first_name}: {location.latitude}, {location.longitude} (updated: {location.last_updated})")
                        else:
                            print(f"      {driver.user.first_name}: No location data")
                    except:
                        print(f"      {driver.user.first_name}: No location data")

def main():
    """Main function to run all checks"""
    
    print("PRODUCTION ALLOCATION DEBUGGING")
    print("=" * 60)
    
    # Check system state
    pending_trips = check_system_state()
    
    # Test allocation
    test_allocation_with_real_data()
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    # Check for common issues
    active_drivers = Driver.objects.filter(status='active')
    if active_drivers.count() == 0:
        print("❌ No active drivers - Add active drivers to the system")
    
    # Check for drivers with recent locations
    time_threshold = timezone.now() - timezone.timedelta(minutes=5)
    drivers_with_recent_locations = Driver.objects.filter(
        status='active',
        location__last_updated__gt=time_threshold
    )
    
    if drivers_with_recent_locations.count() == 0:
        print("❌ No drivers with recent location data - Ensure driver location tracking is working")
    
    # Check Google Maps API
    print("🔍 Google Maps API status: Check logs for API errors")
    
    # Check if there are any pending trips
    pending_trips = Trip.objects.filter(status='pending')
    if pending_trips.count() == 0:
        print("ℹ️  No pending trips - System is working or no requests")
    
    print("\nTo fix allocation issues:")
    print("1. Ensure drivers have 'active' status")
    print("2. Ensure drivers have recent location data (within 5 minutes)")
    print("3. Fix Google Maps API configuration")
    print("4. Check that drivers don't have active trips blocking allocation")
    print("5. Verify pickup locations have valid coordinates")

if __name__ == "__main__":
    main()