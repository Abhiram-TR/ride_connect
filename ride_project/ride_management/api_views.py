#api_views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework.authtoken.models import Token

# Import all your models here
from .models import CustomUser, Driver, Vehicle, Trip, Location
from .serializers import UserSerializer, DriverSerializer, VehicleSerializer, TripSerializer, LocationSerializer
from .services import allocate_trip_to_nearest_driver


# ride_management/api_views.py (login function)
# Make sure the login view has NO permission requirements
@api_view(['POST'])
def login(request):
    """Login API for mobile app"""
    username = request.data.get('username')
    password = request.data.get('password')
    user_type = request.data.get('user_type')
    
    print(f"Login attempt: username={username}, user_type={user_type}")
    
    user = authenticate(username=username, password=password)
    
    if user:
        print(f"User authenticated, user_type in DB: {user.user_type}")
    else:
        print("Authentication failed")
    
    if user and user.user_type == user_type:
        # Create or get token
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)
        
        serializer = UserSerializer(user)
        return Response({
            'success': True,
            'token': token.key,
            'user': serializer.data
        })
    
    return Response({
        'success': False,
        'message': 'Invalid credentials'
    }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_active_trip(request):
    """Get user's active trip"""
    try:
        trip = Trip.objects.filter(
            user=request.user,
            status__in=['pending', 'accepted', 'in_progress']
        ).first()
        
        if trip:
            serializer = TripSerializer(trip)
            return Response({'trip': serializer.data})
        
        return Response({'trip': None})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_ride_history(request):
    """Get user's ride history"""
    try:
        trips = Trip.objects.filter(user=request.user).order_by('-created_at')
        serializer = TripSerializer(trips, many=True)
        return Response({'trips': serializer.data})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_drivers(request):
    """Get nearby available drivers"""
    # This is a simplified version. In production, you'd use geolocation
    drivers = Driver.objects.filter(status='active').select_related('user')[:5]
    
    driver_data = []
    for driver in drivers:
        driver_data.append({
            'id': driver.id,
            'name': f"{driver.user.first_name} {driver.user.last_name}",
            'distance': '0.5 km',  # You'd calculate this based on actual location
            'eta': '5 min'
        })
    
    return Response({'drivers': driver_data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_ride(request):
    """Book a ride"""
    try:
        # Get location objects
        pickup_id = request.data.get('pickup_location_id')
        dropoff_id = request.data.get('dropoff_location_id')
        pickup_time = request.data.get('pickup_time')
        
        # Validate required fields
        if not pickup_id or not dropoff_id or not pickup_time:
            return Response({
                'success': False,
                'message': 'Please provide pickup_location_id, dropoff_location_id, and pickup_time'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create trip
        trip = Trip.objects.create(
            user=request.user,
            pickup_location_id=pickup_id,
            dropoff_location_id=dropoff_id,
            pickup_time=pickup_time,
            status='pending'
        )
        
        # Try to allocate a driver immediately
        allocation_success = False
        allocation_result = None
        
        try:
            allocation_success, allocation_result = allocate_trip_to_nearest_driver(trip.id)
        except Exception as e:
            # If allocation fails, the trip is still created
            print(f"Error in driver allocation: {str(e)}")
        
        serializer = TripSerializer(trip)
        return Response({
            'success': True,
            'trip': serializer.data,
            'driver_assigned': allocation_success,
            'driver_info': allocation_result if allocation_success else None
        })
        
    except Exception as e:
        print(f"Error in book_ride: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

# Driver API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_status(request):
    """Get driver's current status"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    driver = Driver.objects.get(user=request.user)
    return Response({'status': driver.status})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_driver_status(request):
    """Toggle driver online/offline status"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    driver = Driver.objects.get(user=request.user)
    new_status = 'active' if request.data.get('status') else 'inactive'
    driver.status = new_status
    driver.save()
    
    return Response({'status': new_status})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_active_trip(request):
    """Get driver's active trip"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    driver = Driver.objects.get(user=request.user)
    trip = Trip.objects.filter(
        driver=driver,
        status__in=['accepted', 'in_progress']
    ).first()
    
    if trip:
        serializer = TripSerializer(trip)
        return Response({'trip': serializer.data})
    
    return Response({'trip': None})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_stats(request):
    """Get driver's statistics"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    driver = Driver.objects.get(user=request.user)
    
    # Simplified stats - in production, use proper aggregations
    today_trips = Trip.objects.filter(driver=driver, status='completed').count()
    total_trips = Trip.objects.filter(driver=driver, status='completed').count()
    today_earnings = 150.50  # Mock data
    weekly_earnings = 1250.75  # Mock data
    
    return Response({
        'stats': {
            'todayTrips': today_trips,
            'totalTrips': total_trips,
            'todayEarnings': today_earnings,
            'weeklyEarnings': weekly_earnings
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_ride_requests(request):
    """Get pending ride requests for driver"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    # In production, this would include location-based matching
    requests = Trip.objects.filter(
        status='pending',
        driver=None
    ).select_related('user', 'pickup_location', 'dropoff_location')[:5]
    
    request_data = []
    for trip in requests:
        pickup_name = trip.pickup_location.name if trip.pickup_location else trip.pickup_location_text
        dropoff_name = trip.dropoff_location.name if trip.dropoff_location else trip.dropoff_location_text
        
        request_data.append({
            'id': trip.id,
            'pickup_location': pickup_name,
            'dropoff_location': dropoff_name,
            'fare': str(trip.fare),
            'user': trip.user.first_name if trip.user else 'Unknown'
        })
    
    return Response({'requests': request_data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_trip(request, trip_id):
    """Accept a trip request"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        driver = Driver.objects.get(user=request.user)
        trip = Trip.objects.get(id=trip_id, status='pending')
        
        trip.driver = driver
        trip.status = 'accepted'
        trip.save()
        
        serializer = TripSerializer(trip)
        return Response({
            'success': True,
            'trip': serializer.data
        })
    except Trip.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Trip not found or already assigned'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_trip(request, trip_id):
    """Start a trip"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        driver = Driver.objects.get(user=request.user)
        trip = Trip.objects.get(id=trip_id, driver=driver, status='accepted')
        
        trip.status = 'in_progress'
        trip.save()
        
        serializer = TripSerializer(trip)
        return Response({
            'success': True,
            'trip': serializer.data
        })
    except Trip.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Trip not found or not in accepted status'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_trip(request, trip_id):
    """Complete a trip"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        driver = Driver.objects.get(user=request.user)
        trip = Trip.objects.get(id=trip_id, driver=driver, status='in_progress')
        
        trip.status = 'completed'
        trip.actual_arrival = timezone.now()
        trip.save()
        
        serializer = TripSerializer(trip)
        return Response({
            'success': True,
            'trip': serializer.data
        })
    except Trip.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Trip not found or not in progress'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_locations(request):
    """Get list of available locations"""
    try:
        locations = Location.objects.filter(is_active=True)
        airport_locations = locations.filter(is_airport=True)
        other_locations = locations.filter(is_airport=False)
        
        # Use proper serializers
        airport_serializer = LocationSerializer(airport_locations, many=True)
        others_serializer = LocationSerializer(other_locations, many=True)
        
        location_data = {
            'airport': airport_serializer.data,
            'others': others_serializer.data,
        }
        
        return Response(location_data)
    except Exception as e:
        print(f"Error in get_locations: {str(e)}")  # For debugging
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# Add to api_views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_vehicle(request):
    """Get driver's assigned vehicle"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        driver = Driver.objects.get(user=request.user)
        vehicle = Vehicle.objects.filter(driver=driver).first()
        
        if vehicle:
            serializer = VehicleSerializer(vehicle)
            return Response({'vehicle': serializer.data})
        else:
            return Response({'vehicle': None})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_location(request, trip_id):
    """Get driver's location for a trip"""
    try:
        trip = Trip.objects.get(id=trip_id)
        
        # Try to get location from cache
        from django.core.cache import cache
        cache_key = f'driver_location_{trip_id}'
        location_data = cache.get(cache_key)
        
        if location_data:
            return Response({
                'location': {
                    'latitude': location_data['latitude'],
                    'longitude': location_data['longitude'],
                    'timestamp': location_data['timestamp'],
                }
            })
        else:
            # If no location data is found, return default coordinates
            # Center coordinates of Trivandrum
            return Response({
                'location': {
                    'latitude': 8.4834,
                    'longitude': 76.9198,
                    'timestamp': timezone.now().isoformat(),
                }
            })
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_trip(request, trip_id):
    """Cancel a trip"""
    try:
        trip = Trip.objects.get(id=trip_id, user=request.user)
        
        # Only allow cancellation if trip is pending or accepted
        if trip.status not in ['pending', 'accepted']:
            return Response({
                'success': False,
                'message': 'Cannot cancel a trip that is already in progress or completed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trip.status = 'cancelled'
        trip.save()
        
        return Response({
            'success': True,
            'message': 'Trip cancelled successfully'
        })
    except Trip.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Trip not found or you are not authorized to cancel this trip'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Add to api_views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_driver_location(request):
    """Update driver's current location"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        driver = Driver.objects.get(user=request.user)
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if not latitude or not longitude:
            return Response({
                'success': False,
                'message': 'Latitude and longitude are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update or create location
        driver_location, created = DriverLocation.objects.update_or_create(
            driver=driver,
            defaults={
                'latitude': latitude,
                'longitude': longitude
            }
        )
        
        # Update driver status if provided
        if 'status' in request.data:
            driver.status = request.data.get('status')
            driver.save()
        
        return Response({
            'success': True,
            'message': 'Location updated successfully'
        })
        
    except Driver.DoesNotExist:
        return Response({'error': 'Driver not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Add to api_views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_assign_trip(request, trip_id):
    """Auto-assign a trip to the nearest driver"""
    # Admin-only endpoint (you could allow users to trigger this too)
    if request.user.user_type != 'admin' and request.user.user_type != 'user':
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    success, result = allocate_trip_to_nearest_driver(trip_id)
    
    if success:
        return Response({
            'success': True,
            'message': 'Trip assigned successfully',
            'data': result
        })
    else:
        return Response({
            'success': False,
            'message': result
        }, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def allocate_pending_trips(request):
    """Manually trigger allocation of pending trips (admin only)"""
    if request.user.user_type != 'admin':
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    pending_trips = Trip.objects.filter(
        status='pending', 
        driver__isnull=True
    ).order_by('created_at')
    
    results = []
    for trip in pending_trips:
        success, result = allocate_trip_to_nearest_driver(trip.id)
        results.append({
            'trip_id': trip.id,
            'success': success,
            'result': result
        })
    
    return Response({
        'allocated_count': sum(1 for r in results if r['success']),
        'total_pending': len(results),
        'results': results
    })
# Add to api_views.py - new functions and modified functions

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_trip_history(request):
    """Get driver's trip history"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        driver = Driver.objects.get(user=request.user)
        trips = Trip.objects.filter(driver=driver).order_by('-created_at')
        serializer = TripSerializer(trips, many=True)
        return Response({'trips': serializer.data})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_driver_location(request, trip_id=None):
    """Update driver's current location, optionally for a specific trip"""
    if request.user.user_type != 'driver':
        return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        driver = Driver.objects.get(user=request.user)
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        print(f"Location update received: lat={latitude}, lng={longitude}")
        
        if not latitude or not longitude:
            return Response({
                'success': False,
                'message': 'Latitude and longitude are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # General DriverLocation update
        try:
            # Updated for handling the model creation if it doesn't exist
            from django.db.models import Model
            
            # Check if DriverLocation model exists
            if 'DriverLocation' in globals() and issubclass(globals()['DriverLocation'], Model):
                driver_location, created = DriverLocation.objects.update_or_create(
                    driver=driver,
                    defaults={
                        'latitude': latitude,
                        'longitude': longitude,
                        'last_updated': timezone.now()
                    }
                )
                print(f"Updated driver location in database: {created and 'Created new' or 'Updated existing'}")
            else:
                # Fallback to cache if model doesn't exist
                from django.core.cache import cache
                location_data = {
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': timezone.now().isoformat()
                }
                cache.set(f'driver_location_{driver.id}', location_data, timeout=3600)
                print(f"Stored driver location in cache: driver_id={driver.id}")
        except Exception as e:
            # Log the error but continue processing
            print(f"Error updating driver location model: {str(e)}")
        
        # Trip-specific update if trip_id is provided
        if trip_id:
            try:
                trip = Trip.objects.get(id=trip_id, driver=driver)
                # Store in cache using trip_id as key
                from django.core.cache import cache
                cache_key = f'driver_location_{trip_id}'
                cache.set(cache_key, {
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': timezone.now().isoformat(),
                }, timeout=3600)  # 1 hour timeout
                print(f"Stored trip-specific location in cache: trip_id={trip_id}")
            except Trip.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Trip not found or not assigned to this driver'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Update driver status if provided
        previous_status = driver.status
        status_updated = False
        
        if 'status' in request.data:
            status_value = request.data.get('status')
            print(f"Received status value: {status_value}, type: {type(status_value)}")
            
            # Convert various formats to proper driver status
            if isinstance(status_value, bool):
                driver.status = 'active' if status_value else 'inactive'
                status_updated = True
            elif isinstance(status_value, str):
                if status_value.lower() in ['true', 'active', '1', 'on']:
                    driver.status = 'active'
                    status_updated = True
                elif status_value.lower() in ['false', 'inactive', '0', 'off']:
                    driver.status = 'inactive'
                    status_updated = True
                else:
                    # For other string values, only accept valid status values
                    if status_value in ['active', 'inactive', 'on_trip']:
                        driver.status = status_value
                        status_updated = True
            elif status_value == 1 or status_value == "1":
                driver.status = 'active'
                status_updated = True
            elif status_value == 0 or status_value == "0":
                driver.status = 'inactive'
                status_updated = True
            
            if status_updated:
                print(f"Status updated: {previous_status} -> {driver.status}")
                driver.save()
            else:
                print(f"Status not updated, invalid value: {status_value}")
        
        return Response({
            'success': True,
            'message': 'Location updated successfully',
            'status': driver.status,
            'status_updated': status_updated
        })
        
    except Driver.DoesNotExist:
        return Response({
            'error': 'Driver not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Unexpected error in update_driver_location: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Refactor the auto_assign_trip function to ensure it's not duplicated
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_assign_trip(request, trip_id):
    """Auto-assign a trip to the nearest driver"""
    # Check permissions - admin or user who owns the trip
    if request.user.user_type != 'admin':
        try:
            trip = Trip.objects.get(id=trip_id)
            if request.user.user_type != 'user' or request.user.id != trip.user.id:
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        except Trip.DoesNotExist:
            return Response({'error': 'Trip not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        success, result = allocate_trip_to_nearest_driver(trip_id)
        
        if success:
            return Response({
                'success': True,
                'message': 'Trip assigned successfully',
                'data': result
            })
        else:
            return Response({
                'success': False,
                'message': result
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)