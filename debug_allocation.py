#!/usr/bin/env python3
"""
Debug script to test the driver allocation logic
"""

import os
import sys
import django

# Add the Django project to the Python path
sys.path.append('/Users/abhiramt/Desktop/work_2/ride_management_project/ride_project')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ride_project.settings')
django.setup()

from ride_management.models import Driver, Trip, DriverLocation
from ride_management.services import find_nearest_driver
from django.utils import timezone
import logging

# Set up logging to see debug output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_allocation():
    """Debug the allocation system"""
    
    # Find any trip to test with
    trips = Trip.objects.all()
    print(f"Total trips: {trips.count()}")
    
    for trip in trips[:5]:
        print(f"Trip {trip.id}: status={trip.status}, pickup={trip.pickup_location}")
    
    # Find a pending trip or use any trip
    pending_trip = Trip.objects.filter(status='pending').first()
    if not pending_trip:
        pending_trip = Trip.objects.first()
        if not pending_trip:
            print("No trips found")
            return
        print(f"Using trip with status: {pending_trip.status}")
    else:
        print("Found pending trip")
    
    print(f"Testing allocation for trip {pending_trip.id}")
    print(f"Pickup location: {pending_trip.pickup_location}")
    print(f"Pickup coordinates: {pending_trip.pickup_location.latitude}, {pending_trip.pickup_location.longitude}")
    
    # Get all active drivers with their locations
    active_drivers = Driver.objects.filter(status='active').select_related('location')
    
    print(f"\nActive drivers ({active_drivers.count()}):")
    for driver in active_drivers:
        if hasattr(driver, 'location') and driver.location:
            print(f"Driver {driver.id}: {driver.location.latitude}, {driver.location.longitude} (updated: {driver.location.last_updated})")
        else:
            print(f"Driver {driver.id}: No location data")
    
    # Test the allocation
    print("\n" + "="*50)
    print("TESTING ALLOCATION")
    print("="*50)
    
    nearest_driver, result = find_nearest_driver(pending_trip)
    
    if nearest_driver:
        print(f"✓ Found nearest driver: {nearest_driver.id}")
        print(f"Distance: {result}km")
        if hasattr(nearest_driver, 'location') and nearest_driver.location:
            print(f"Driver location: {nearest_driver.location.latitude}, {nearest_driver.location.longitude}")
    else:
        print(f"✗ No driver found: {result}")

if __name__ == "__main__":
    debug_allocation()