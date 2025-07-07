from django.core.management.base import BaseCommand
from django.conf import settings
from ride_management.services import get_road_distance_google_maps
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test Google Maps API configuration'

    def handle(self, *args, **options):
        """Test Google Maps API with sample coordinates"""
        
        self.stdout.write("Testing Google Maps API Configuration...")
        
        # Check if API key is configured
        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR("Google Maps API key not configured in settings"))
            return
        
        self.stdout.write(f"API Key: {api_key[:10]}...")
        
        # Test with sample coordinates (close to your test area)
        test_coordinates = [
            (8.482959, 76.916095),  # Pickup location
            (8.483000, 76.916200),  # Close driver
        ]
        
        self.stdout.write("Testing distance calculation...")
        
        origin_lat, origin_lng = test_coordinates[0]
        dest_lat, dest_lng = test_coordinates[1]
        
        distance, duration = get_road_distance_google_maps(
            origin_lat, origin_lng, dest_lat, dest_lng
        )
        
        if distance is not None:
            self.stdout.write(self.style.SUCCESS(f"✓ API working! Distance: {distance:.2f}km, Duration: {duration:.1f}min"))
        else:
            self.stdout.write(self.style.ERROR("✗ API failed - check the logs above for details"))
            
        self.stdout.write("\nTo fix Google Maps API issues:")
        self.stdout.write("1. Check API key permissions in Google Cloud Console")
        self.stdout.write("2. Ensure Distance Matrix API is enabled")
        self.stdout.write("3. Check billing is set up correctly")
        self.stdout.write("4. Verify any IP or domain restrictions")
        self.stdout.write("5. Check API quotas and limits")
        
        # Provide instructions for fixing the API
        self.stdout.write("\nAlternative solutions:")
        self.stdout.write("1. Use a different Google Maps API key")
        self.stdout.write("2. Use alternative mapping services (OpenStreetMap, MapBox)")
        self.stdout.write("3. Improve the Haversine fallback with better multipliers")