from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import CustomUser, Driver, Vehicle, Trip,Location
from .forms import DriverForm, VehicleForm, TripForm, UserForm ,LocationForm 
from django.contrib import messages

@login_required
def dashboard(request):
    """Dashboard page"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    context = {
        'total_drivers': Driver.objects.count(),
        'active_drivers': Driver.objects.filter(status='active').count(),
        'total_vehicles': Vehicle.objects.count(),
        'available_vehicles': Vehicle.objects.filter(status='available').count(),
        'total_trips': Trip.objects.count(),
        'pending_trips': Trip.objects.filter(status='pending').count(),
        'completed_trips': Trip.objects.filter(status='completed').count(),
        'total_users': CustomUser.objects.filter(user_type='user').count(),
        # Add location statistics
        'total_locations': Location.objects.count(),
        'airport_locations': Location.objects.filter(is_airport=True, is_active=True).count(),
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
def drivers_list(request):
    """Drivers management page"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    drivers = Driver.objects.all()
    return render(request, 'admin/drivers.html', {'drivers': drivers})

@login_required
def add_driver(request):
    """Add new driver"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('drivers_list')
    else:
        form = DriverForm()
    
    return render(request, 'admin/add_driver.html', {'form': form})

@login_required
def edit_driver(request, driver_id):
    """Edit driver details"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    driver = get_object_or_404(Driver, id=driver_id)
    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            try:
                form.save()
                return redirect('drivers_list')
            except Exception as e:
                # Handle unique constraint violations
                if 'unique constraint' in str(e).lower() or 'duplicate key' in str(e).lower():
                    if 'username' in str(e).lower():
                        form.add_error('username', 'This username is already taken')
                    elif 'email' in str(e).lower():
                        form.add_error('email', 'This email is already registered')
                    else:
                        form.add_error(None, f"Database error: {str(e)}")
                else:
                    form.add_error(None, f"Error saving driver: {str(e)}")
    else:
        form = DriverForm(instance=driver)
    
    return render(request, 'admin/edit_driver.html', {'form': form, 'driver': driver})
    

@login_required
def vehicles_list(request):
    """Vehicles management page"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    vehicles = Vehicle.objects.all()
    return render(request, 'admin/vehicles.html', {'vehicles': vehicles})

@login_required
def add_vehicle(request):
    """Add new vehicle"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('vehicles_list')
    else:
        form = VehicleForm()
    
    return render(request, 'admin/add_vehicle.html', {'form': form})

@login_required
def edit_vehicle(request, vehicle_id):
    """Edit vehicle details"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            return redirect('vehicles_list')
    else:
        form = VehicleForm(instance=vehicle)
    
    return render(request, 'admin/edit_vehicle.html', {'form': form, 'vehicle': vehicle})

@login_required
def trips_list(request):
    """Trips management page"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    # Use select_related to fetch related objects in a single query
    trips = Trip.objects.all().order_by('-created_at').select_related(
        'user', 'driver__user', 'vehicle'
    )
    
    # For each trip that has a driver but no explicitly assigned vehicle,
    # try to find the driver's vehicle
    for trip in trips:
        if trip.driver and not trip.vehicle:
            # Try to get the driver's assigned vehicle
            vehicle = Vehicle.objects.filter(driver=trip.driver).first()
            if vehicle:
                trip.driver_vehicle = vehicle
    
    return render(request, 'admin/trips.html', {'trips': trips})

@login_required
def trip_detail(request, trip_id):
    """Trip detail page"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    trip = get_object_or_404(Trip.objects.select_related(
        'user', 'driver__user', 'vehicle'
    ), id=trip_id)
    
    # If trip has a driver but no vehicle, try to find the driver's vehicle
    if trip.driver and not trip.vehicle:
        vehicle = Vehicle.objects.filter(driver=trip.driver).first()
        if vehicle:
            trip.driver_vehicle = vehicle
    
    return render(request, 'admin/trip_detail.html', {'trip': trip})

@login_required
def users_list(request):
    """Users list page"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    users = CustomUser.objects.filter(user_type='user')
    return render(request, 'admin/users.html', {'users': users})

@login_required
def add_user(request):
    """Add new user"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f"User '{user.username}' created successfully")
                return redirect('users_list')
            except Exception as e:
                messages.error(request, f"Error creating user: {str(e)}")
                print(f"Error creating user: {str(e)}")
        else:
            # Print form errors for debugging
            print(f"Form errors: {form.errors}")
    else:
        form = UserForm()
    
    return render(request, 'admin/add_user.html', {'form': form})

@login_required
def edit_user(request, user_id):
    """Edit user details"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"User '{user.username}' updated successfully")
                return redirect('users_list')
            except Exception as e:
                messages.error(request, f"Error updating user: {str(e)}")
                print(f"Error updating user: {str(e)}")
        else:
            # Print form errors for debugging
            print(f"Form errors: {form.errors}")
    else:
        form = UserForm(instance=user)
    
    return render(request, 'admin/edit_user.html', {'form': form, 'user_obj': user})

@login_required
def update_trip_status(request, trip_id):
    """Update trip status"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    trip = get_object_or_404(Trip, id=trip_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['cancelled', 'completed']:
            trip.status = new_status
            trip.save()
    
    return redirect('trip_detail', trip_id=trip_id)

def admin_logout(request):
    """Logout view"""
    logout(request)
    return redirect('login')# Add these functions to your ride_management/views.py file

@login_required
def locations_list(request):
    """Locations management page"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    locations = Location.objects.all()
    return render(request, 'admin/locations.html', {'locations': locations})

@login_required
def add_location(request):
    """Add new location"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('locations_list')
    else:
        form = LocationForm()
    
    return render(request, 'admin/add_location.html', {'form': form})

@login_required
def edit_location(request, location_id):
    """Edit location details"""
    if request.user.user_type != 'admin':
        return redirect('login')
    
    location = get_object_or_404(Location, id=location_id)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect('locations_list')
    else:
        form = LocationForm(instance=location)
    
    return render(request, 'admin/edit_location.html', {'form': form, 'location': location})