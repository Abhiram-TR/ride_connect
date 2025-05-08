# ride_management/services.py

from .models import Driver, Trip, DriverLocation
from django.utils import timezone
import math

def find_nearest_driver(trip):
    """Find the nearest active driver for a trip"""
    try:
        # Get trip pickup coordinates
        pickup_latitude = float(trip.pickup_location.latitude)
        pickup_longitude = float(trip.pickup_location.longitude)
        
        # Get all active drivers with location info, updated in the last 5 minutes
        five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
        
        active_drivers = Driver.objects.filter(
            status='active',
        ).select_related('user')
        
        if not active_drivers.exists():
            return None, "No active drivers found"
        
        # Find the nearest driver
        nearest_driver = None
        min_distance = float('inf')
        
        for driver in active_drivers:
            # Skip drivers who already have an active trip
            active_trip_exists = Trip.objects.filter(
                driver=driver,
                status__in=['accepted', 'in_progress']
            ).exists()
            
            if active_trip_exists:
                continue
            
            # For now, use a simplified distance calculation
            # In a real app, you'd use the actual driver locations from DriverLocation model
            # This is a placeholder implementation
            driver_latitude = 8.4834  # Default/placeholder latitude
            driver_longitude = 76.9198  # Default/placeholder longitude
            
            # Calculate simple distance (this is just for testing)
            distance = math.sqrt(
                (pickup_latitude - driver_latitude)**2 + 
                (pickup_longitude - driver_longitude)**2
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_driver = driver
        
        if nearest_driver:
            return nearest_driver, min_distance
        else:
            return None, "No available drivers found"
    
    except Exception as e:
        return None, str(e)

def allocate_trip_to_nearest_driver(trip_id):
    """Allocate a trip to the nearest available driver"""
    try:
        trip = Trip.objects.get(id=trip_id, status='pending', driver__isnull=True)
        
        # Find the nearest driver
        result = find_nearest_driver(trip)
        if not result or not result[0]:
            return False, result[1] if result else "Error finding nearest driver"
        
        nearest_driver, distance = result
        
        # Assign the driver to the trip
        trip.driver = nearest_driver
        trip.status = 'accepted'
        trip.save()
        
        return True, {
            'driver_id': nearest_driver.id,
            'driver_name': f"{nearest_driver.user.first_name} {nearest_driver.user.last_name}",
            'distance': distance
        }
        
    except Trip.DoesNotExist:
        return False, "Trip not found or already assigned"
    except Exception as e:
        return False, str(e)