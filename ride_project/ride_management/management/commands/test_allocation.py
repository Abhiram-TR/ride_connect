# Test allocation system - management/commands/test_allocation.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from ride_management.models import Trip, Driver, Location, DriverLocation
from ride_management.services import allocate_trip_to_nearest_driver, get_driver_availability_stats
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test and debug the trip allocation system'

    def add_arguments(self, parser):
        parser.add_argument('--trip-id', type=int, help='Test allocation for specific trip ID')
        parser.add_argument('--stats', action='store_true', help='Show driver availability stats')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    def handle(self, *args, **options):
        if options['debug']:
            logging.basicConfig(level=logging.DEBUG)
        
        self.stdout.write(self.style.SUCCESS('=== Trip Allocation Test ==='))
        
        if options['stats']:
            self.show_stats()
        
        if options['trip_id']:
            self.test_specific_trip(options['trip_id'])
        else:
            self.test_all_pending_trips()

    def show_stats(self):
        """Show driver availability statistics"""
        self.stdout.write(self.style.SUCCESS('\n=== Driver Availability Stats ==='))
        
        stats = get_driver_availability_stats()
        for key, value in stats.items():
            self.stdout.write(f"{key}: {value}")
        
        # Show location data status
        self.stdout.write(f"\nDrivers with location data: {DriverLocation.objects.count()}")
        
        # Show recent location updates
        recent_threshold = timezone.now() - timezone.timedelta(minutes=5)
        recent_locations = DriverLocation.objects.filter(
            last_updated__gte=recent_threshold
        ).count()
        self.stdout.write(f"Drivers with recent location updates (5 min): {recent_locations}")

    def test_specific_trip(self, trip_id):
        """Test allocation for a specific trip"""
        self.stdout.write(self.style.SUCCESS(f'\n=== Testing Trip {trip_id} ==='))
        
        try:
            trip = Trip.objects.get(id=trip_id)
            self.stdout.write(f"Trip status: {trip.status}")
            self.stdout.write(f"Trip pickup: {trip.pickup_location}")
            self.stdout.write(f"Trip dropoff: {trip.dropoff_location}")
            
            if trip.pickup_location:
                self.stdout.write(f"Pickup coordinates: {trip.pickup_location.latitude}, {trip.pickup_location.longitude}")
            
            success, result = allocate_trip_to_nearest_driver(trip_id)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f"✓ Trip allocated successfully!"))
                self.stdout.write(f"Driver: {result['driver_name']}")
                self.stdout.write(f"Distance: {result['distance_km']} km")
                self.stdout.write(f"ETA: {result['estimated_arrival_minutes']} minutes")
            else:
                self.stdout.write(self.style.ERROR(f"✗ Allocation failed: {result}"))
                
        except Trip.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Trip {trip_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def test_all_pending_trips(self):
        """Test allocation for all pending trips"""
        self.stdout.write(self.style.SUCCESS('\n=== Testing All Pending Trips ==='))
        
        pending_trips = Trip.objects.filter(
            status='pending',
            driver__isnull=True
        ).order_by('created_at')
        
        if not pending_trips.exists():
            self.stdout.write("No pending trips found")
            return
        
        for trip in pending_trips:
            self.stdout.write(f"\nTesting trip {trip.id}...")
            success, result = allocate_trip_to_nearest_driver(trip.id)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f"✓ Trip {trip.id} allocated to {result['driver_name']}"))
            else:
                self.stdout.write(self.style.WARNING(f"✗ Trip {trip.id} failed: {result}"))