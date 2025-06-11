# ride_management/services.py

from .models import Driver, Trip, DriverLocation
from django.utils import timezone
from django.db.models import Q
import math
import logging

logger = logging.getLogger(__name__)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r

def find_nearest_driver(trip, max_radius_km=10):
    """
    Find the nearest active driver for a trip within a specified radius
    
    Args:
        trip: Trip object
        max_radius_km: Maximum search radius in kilometers (default: 10km)
    
    Returns:
        tuple: (Driver object or None, distance or error message)
    """
    try:
        # Get trip pickup coordinates
        pickup_latitude = float(trip.pickup_location.latitude)
        pickup_longitude = float(trip.pickup_location.longitude)
        
        # Define time threshold for recent location updates
        location_update_threshold = timezone.now() - timezone.timedelta(minutes=5)
        
        # Get all active drivers with recent location data
        active_drivers = Driver.objects.filter(
            status='active'
        ).select_related('user').prefetch_related('driverlocation_set')
        
        if not active_drivers.exists():
            return None, "No active drivers found"
        
        # Find the nearest driver
        nearest_driver = None
        min_distance = float('inf')
        candidates_found = 0
        
        for driver in active_drivers:
            try:
                # Skip drivers who already have an active trip
                active_trip_exists = Trip.objects.filter(
                    driver=driver,
                    status__in=['accepted', 'in_progress', 'arrived']
                ).exists()
                
                if active_trip_exists:
                    continue
                
                # Get driver's most recent location within the time threshold
                try:
                    driver_location = DriverLocation.objects.filter(
                        driver=driver,
                        timestamp__gte=location_update_threshold
                    ).latest('timestamp')
                except DriverLocation.DoesNotExist:
                    # Skip drivers without recent location data
                    logger.debug(f"Driver {driver.id} has no recent location data")
                    continue
                
                driver_latitude = float(driver_location.latitude)
                driver_longitude = float(driver_location.longitude)
                
                # Calculate distance using Haversine formula
                distance = haversine_distance(
                    pickup_latitude, pickup_longitude,
                    driver_latitude, driver_longitude
                )
                
                candidates_found += 1
                
                # Check if driver is within acceptable radius
                if distance <= max_radius_km and distance < min_distance:
                    min_distance = distance
                    nearest_driver = driver
                    
            except (ValueError, TypeError) as e:
                logger.error(f"Error processing driver {driver.id}: {str(e)}")
                continue
        
        if nearest_driver:
            logger.info(f"Found nearest driver {nearest_driver.id} at distance {min_distance:.2f}km")
            return nearest_driver, round(min_distance, 2)
        else:
            if candidates_found == 0:
                return None, "No drivers with recent location data found"
            else:
                return None, f"No drivers found within {max_radius_km}km radius"
    
    except Exception as e:
        logger.error(f"Error in find_nearest_driver: {str(e)}")
        return None, f"Error finding nearest driver: {str(e)}"

def get_driver_availability_stats():
    """
    Get statistics about driver availability
    
    Returns:
        dict: Statistics about drivers and their status
    """
    try:
        location_update_threshold = timezone.now() - timezone.timedelta(minutes=5)
        
        total_drivers = Driver.objects.count()
        active_drivers = Driver.objects.filter(status='active').count()
        
        # Drivers with recent location updates
        drivers_with_recent_location = Driver.objects.filter(
            driverlocation__timestamp__gte=location_update_threshold
        ).distinct().count()
        
        # Available drivers (active, no current trip, recent location)
        available_drivers = Driver.objects.filter(
            status='active'
        ).exclude(
            trip__status__in=['accepted', 'in_progress', 'arrived']
        ).filter(
            driverlocation__timestamp__gte=location_update_threshold
        ).distinct().count()
        
        return {
            'total_drivers': total_drivers,
            'active_drivers': active_drivers,
            'drivers_with_recent_location': drivers_with_recent_location,
            'available_drivers': available_drivers,
            'location_update_threshold_minutes': 5
        }
    except Exception as e:
        logger.error(f"Error getting driver stats: {str(e)}")
        return {}

def allocate_trip_to_nearest_driver(trip_id, max_radius_km=10):
    """
    Allocate a trip to the nearest available driver within specified radius
    
    Args:
        trip_id: ID of the trip to allocate
        max_radius_km: Maximum search radius in kilometers
    
    Returns:
        tuple: (success: bool, result: dict or error message)
    """
    try:
        # Get the trip
        trip = Trip.objects.select_related('pickup_location').get(
            id=trip_id, 
            status='pending', 
            driver__isnull=True
        )
        
        # Find the nearest driver
        result = find_nearest_driver(trip, max_radius_km)
        
        if not result or not result[0]:
            error_msg = result[1] if result else "Error finding nearest driver"
            logger.warning(f"No driver found for trip {trip_id}: {error_msg}")
            return False, error_msg
        
        nearest_driver, distance = result
        
        # Double-check driver availability before assignment
        active_trip_exists = Trip.objects.filter(
            driver=nearest_driver,
            status__in=['accepted', 'in_progress', 'arrived']
        ).exists()
        
        if active_trip_exists:
            logger.warning(f"Driver {nearest_driver.id} became unavailable during allocation")
            return False, "Selected driver became unavailable"
        
        # Assign the driver to the trip
        trip.driver = nearest_driver
        trip.status = 'accepted'
        trip.assigned_at = timezone.now()
        trip.save()
        
        # Log the successful allocation
        logger.info(f"Trip {trip_id} allocated to driver {nearest_driver.id} (distance: {distance}km)")
        
        return True, {
            'driver_id': nearest_driver.id,
            'driver_name': f"{nearest_driver.user.first_name} {nearest_driver.user.last_name}",
            'driver_phone': nearest_driver.user.phone if hasattr(nearest_driver.user, 'phone') else None,
            'vehicle_info': {
                'license_plate': nearest_driver.license_plate,
                'vehicle_model': nearest_driver.vehicle_model,
                'vehicle_color': nearest_driver.vehicle_color
            } if hasattr(nearest_driver, 'license_plate') else None,
            'distance_km': distance,
            'estimated_arrival_minutes': max(int(distance * 2), 5)  # Rough estimate: 2 min per km, min 5 min
        }
        
    except Trip.DoesNotExist:
        return False, "Trip not found or already assigned"
    except Exception as e:
        logger.error(f"Error allocating trip {trip_id}: {str(e)}")
        return False, f"Error during allocation: {str(e)}"

def bulk_allocate_pending_trips(max_radius_km=10, max_trips=50):
    """
    Allocate multiple pending trips to available drivers
    Useful for batch processing or system recovery
    
    Args:
        max_radius_km: Maximum search radius for each trip
        max_trips: Maximum number of trips to process in one batch
    
    Returns:
        dict: Summary of allocation results
    """
    try:
        # Get pending trips
        pending_trips = Trip.objects.filter(
            status='pending',
            driver__isnull=True
        ).select_related('pickup_location')[:max_trips]
        
        results = {
            'total_processed': 0,
            'successful_allocations': 0,
            'failed_allocations': 0,
            'errors': []
        }
        
        for trip in pending_trips:
            results['total_processed'] += 1
            success, result = allocate_trip_to_nearest_driver(trip.id, max_radius_km)
            
            if success:
                results['successful_allocations'] += 1
            else:
                results['failed_allocations'] += 1
                results['errors'].append({
                    'trip_id': trip.id,
                    'error': result
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Error in bulk allocation: {str(e)}")
        return {
            'total_processed': 0,
            'successful_allocations': 0,
            'failed_allocations': 0,
            'errors': [f"Bulk allocation error: {str(e)}"]
        }

def cancel_trip_allocation(trip_id, reason=""):
    """
    Cancel a trip allocation and make the driver available again
    
    Args:
        trip_id: ID of the trip to cancel
        reason: Reason for cancellation
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        trip = Trip.objects.get(id=trip_id)
        
        if trip.status not in ['accepted', 'in_progress']:
            return False, f"Cannot cancel trip with status: {trip.status}"
        
        # Free up the driver
        driver = trip.driver
        trip.driver = None
        trip.status = 'cancelled'
        trip.cancelled_at = timezone.now()
        trip.cancellation_reason = reason
        trip.save()
        
        logger.info(f"Trip {trip_id} cancelled, driver {driver.id if driver else 'None'} freed up")
        
        return True, "Trip cancelled successfully"
        
    except Trip.DoesNotExist:
        return False, "Trip not found"
    except Exception as e:
        logger.error(f"Error cancelling trip {trip_id}: {str(e)}")
        return False, f"Error cancelling trip: {str(e)}"