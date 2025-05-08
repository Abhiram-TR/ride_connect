# Create a management command in management/commands/allocate_trips.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from ride_management.models import Trip
from ride_management.services import allocate_trip_to_nearest_driver
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Continuously allocate pending trips to nearest drivers'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting trip allocation service'))
        
        while True:
            try:
                # Get all pending trips without drivers
                pending_trips = Trip.objects.filter(
                    status='pending', 
                    driver__isnull=True
                ).order_by('created_at')
                
                for trip in pending_trips:
                    # Skip trips that have been pending for more than 30 minutes
                    time_diff = timezone.now() - trip.created_at
                    if time_diff.total_seconds() > 30 * 60:
                        self.stdout.write(f"Trip {trip.id} has been pending for too long. Skipping.")
                        continue
                    
                    self.stdout.write(f"Attempting to allocate trip {trip.id}")
                    success, result = allocate_trip_to_nearest_driver(trip.id)
                    
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Trip {trip.id} assigned to driver {result['driver_name']}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Couldn't assign trip {trip.id}: {result}"
                            )
                        )
                
                # Sleep for 10 seconds before checking again
                time.sleep(10)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error in trip allocation service: {str(e)}")
                )
                # Sleep for a bit longer if there was an error
                time.sleep(30)