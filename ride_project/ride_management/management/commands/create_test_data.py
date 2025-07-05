# Test data creation - management/commands/create_test_data.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from ride_management.models import CustomUser, Driver, Location, DriverLocation, Trip
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Create test data for driver allocation testing'

    def add_arguments(self, parser):
        parser.add_argument('--drivers', type=int, default=5, help='Number of test drivers to create')
        parser.add_argument('--locations', action='store_true', help='Create test locations')
        parser.add_argument('--trips', type=int, default=3, help='Number of test trips to create')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data...'))
        
        if options['locations']:
            self.create_test_locations()
        
        self.create_test_drivers(options['drivers'])
        self.create_test_trips(options['trips'])
        
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))

    def create_test_locations(self):
        """Create test locations with coordinates"""
        locations_data = [
            {'name': 'Trivandrum International Airport', 'address': 'Airport Road, Thiruvananthapuram', 
             'latitude': 8.4821, 'longitude': 76.9199, 'is_airport': True},
            {'name': 'Central Railway Station', 'address': 'Thampanoor, Thiruvananthapuram', 
             'latitude': 8.4900, 'longitude': 76.9523, 'is_airport': False},
            {'name': 'Technopark', 'address': 'Kazhakoottam, Thiruvananthapuram', 
             'latitude': 8.5506, 'longitude': 76.8784, 'is_airport': False},
            {'name': 'Medical College', 'address': 'Medical College Road, Thiruvananthapuram', 
             'latitude': 8.5265, 'longitude': 76.9443, 'is_airport': False},
            {'name': 'Kovalam Beach', 'address': 'Kovalam, Thiruvananthapuram', 
             'latitude': 8.4004, 'longitude': 76.9786, 'is_airport': False},
        ]
        
        for loc_data in locations_data:
            location, created = Location.objects.get_or_create(
                name=loc_data['name'],
                defaults=loc_data
            )
            if created:
                self.stdout.write(f"Created location: {location.name}")

    def create_test_drivers(self, count):
        """Create test drivers with locations"""
        # Base coordinates for Trivandrum
        base_lat = 8.4834
        base_lon = 76.9198
        
        for i in range(count):
            # Create user
            username = f"testdriver{i+1}"
            user, created = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'testdriver{i+1}@example.com',
                    'first_name': f'Driver{i+1}',
                    'last_name': 'Test',
                    'user_type': 'driver',
                    'phone': f'98470000{i+1:02d}'
                }
            )
            
            if created:
                user.set_password('testpass123')
                user.save()
            
            # Create driver
            driver, created = Driver.objects.get_or_create(
                user=user,
                defaults={
                    'license_number': f'KL01{i+1:04d}',
                    'license_expiry': timezone.now().date() + timedelta(days=365),
                    'status': 'active'
                }
            )
            
            if created:
                self.stdout.write(f"Created driver: {driver}")
            
            # Create driver location (random within 10km of Trivandrum center)
            lat_offset = random.uniform(-0.05, 0.05)  # ~5km range
            lon_offset = random.uniform(-0.05, 0.05)  # ~5km range
            
            location, created = DriverLocation.objects.update_or_create(
                driver=driver,
                defaults={
                    'latitude': base_lat + lat_offset,
                    'longitude': base_lon + lon_offset,
                    'last_updated': timezone.now()
                }
            )
            
            if created:
                self.stdout.write(f"Created location for driver {driver.id}")

    def create_test_trips(self, count):
        """Create test pending trips"""
        locations = list(Location.objects.all()[:4])  # Get first 4 locations
        
        if len(locations) < 2:
            self.stdout.write(self.style.WARNING('Need at least 2 locations to create trips'))
            return
        
        # Create a test user
        user, created = CustomUser.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'testuser@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'user_type': 'user',
                'phone': '9876543210'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f"Created test user: {user}")
        
        for i in range(count):
            pickup = random.choice(locations)
            dropoff = random.choice([loc for loc in locations if loc != pickup])
            
            trip, created = Trip.objects.get_or_create(
                user=user,
                pickup_location=pickup,
                dropoff_location=dropoff,
                pickup_time=timezone.now() + timedelta(minutes=random.randint(15, 60)),
                defaults={
                    'status': 'pending',
                    'fare': 150.00
                }
            )
            
            if created:
                self.stdout.write(f"Created trip: {pickup.name} → {dropoff.name}")