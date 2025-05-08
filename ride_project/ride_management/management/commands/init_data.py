from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ride_management.models import Driver, Vehicle, Trip

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialize the database with sample data'

    def handle(self, *args, **options):
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                user_type='admin'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        
        # Create sample drivers
        sample_drivers = [
            {'username': 'driver1', 'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com', 'phone': '1234567890', 'license_number': 'DL123456'},
            {'username': 'driver2', 'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane@example.com', 'phone': '9876543210', 'license_number': 'DL654321'},
        ]
        
        for driver_data in sample_drivers:
            if not User.objects.filter(username=driver_data['username']).exists():
                user = User.objects.create_user(
                    username=driver_data['username'],
                    email=driver_data['email'],
                    password='driver123',
                    first_name=driver_data['first_name'],
                    last_name=driver_data['last_name'],
                    phone=driver_data['phone'],
                    user_type='driver'
                )
                Driver.objects.create(
                    user=user,
                    license_number=driver_data['license_number'],
                    license_expiry='2025-12-31',
                    status='active'
                )
                self.stdout.write(self.style.SUCCESS(f'Created driver: {driver_data["username"]}'))
        
        # Create sample vehicles
        sample_vehicles = [
            {'plate_number': 'ABC123', 'model': 'Toyota Prius', 'year': 2022, 'color': 'White', 'seats': 4},
            {'plate_number': 'XYZ789', 'model': 'Honda Civic', 'year': 2023, 'color': 'Black', 'seats': 4},
        ]
        
        for vehicle_data in sample_vehicles:
            if not Vehicle.objects.filter(plate_number=vehicle_data['plate_number']).exists():
                Vehicle.objects.create(**vehicle_data)
                self.stdout.write(self.style.SUCCESS(f'Created vehicle: {vehicle_data["plate_number"]}'))
        
        # Create sample users
        sample_users = [
            {'username': 'user1', 'first_name': 'Alice', 'last_name': 'Johnson', 'email': 'alice@example.com', 'phone': '5555555555'},
            {'username': 'user2', 'first_name': 'Bob', 'last_name': 'Wilson', 'email': 'bob@example.com', 'phone': '4444444444'},
        ]
        
        for user_data in sample_users:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password='user123',
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    phone=user_data['phone'],
                    user_type='user'
                )
                self.stdout.write(self.style.SUCCESS(f'Created user: {user_data["username"]}'))
        
        self.stdout.write(self.style.SUCCESS('Database initialization completed!'))