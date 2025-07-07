#!/usr/bin/env python3
"""
Test script to verify allocation works with configurable location freshness
"""

import os
import sys
import django

# Add the Django project to the Python path
sys.path.append('/Users/abhiramt/Desktop/work_2/ride_management_project/ride_project')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ride_project.settings')
django.setup()

from ride_management.models import Trip
from ride_management.services import find_nearest_driver, allocate_trip_to_nearest_driver

def test_allocation_fix():
    """Test allocation with flexible location freshness"""
    
    print("Testing allocation with flexible location freshness...")
    
    # Get a pending trip
    pending_trip = Trip.objects.filter(status='pending').first()
    if not pending_trip:
        print("No pending trips found")
        return
    
    print(f"Testing trip {pending_trip.id}")
    
    # Test with default 5-minute freshness (should fail)
    print("\n1. Testing with 5-minute location freshness (default):")
    driver, result = find_nearest_driver(pending_trip, debug=True)
    if driver:
        print(f"   ✓ Found driver: {driver.user.first_name}")
    else:
        print(f"   ✗ No driver found: {result}")
    
    # Test with 60-minute freshness (should work)
    print("\n2. Testing with 60-minute location freshness:")
    driver, result = find_nearest_driver(pending_trip, debug=True, location_freshness_minutes=60)
    if driver:
        print(f"   ✓ Found driver: {driver.user.first_name}")
        print(f"   Distance: {result}km")
    else:
        print(f"   ✗ No driver found: {result}")
    
    # Test with 24-hour freshness (should definitely work)
    print("\n3. Testing with 24-hour location freshness:")
    driver, result = find_nearest_driver(pending_trip, debug=True, location_freshness_minutes=1440)
    if driver:
        print(f"   ✓ Found driver: {driver.user.first_name}")
        print(f"   Distance: {result}km")
    else:
        print(f"   ✗ No driver found: {result}")
    
    # Test actual allocation with longer freshness
    print("\n4. Testing actual allocation with 60-minute freshness:")
    success, message = allocate_trip_to_nearest_driver(
        pending_trip.id, 
        max_radius_km=10, 
        location_freshness_minutes=60
    )
    
    if success:
        print(f"   ✅ Allocation successful: {message}")
        
        # Reload trip to see changes
        pending_trip.refresh_from_db()
        print(f"   Trip status: {pending_trip.status}")
        print(f"   Assigned driver: {pending_trip.driver.user.first_name if pending_trip.driver else 'None'}")
    else:
        print(f"   ❌ Allocation failed: {message}")

if __name__ == "__main__":
    test_allocation_fix()