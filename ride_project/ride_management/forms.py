from django import forms
from .models import CustomUser, Driver, Vehicle, Trip, Location 
from django.contrib.auth.forms import UserCreationForm

# ride_management/forms.py
from django import forms
from .models import CustomUser, Driver, Vehicle, Trip

# forms.py
class DriverForm(forms.ModelForm):
    """Form for creating/editing drivers"""
    username = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput(), required=False,
                             help_text="Leave blank to keep the current password")
    
    class Meta:
        model = Driver
        fields = ['license_number', 'license_expiry', 'status']
        widgets = {
            'license_expiry': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # Edit form
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = self.instance.user.phone
    
    def save(self, commit=True):
        driver = super().save(commit=False)
        
        if driver.pk:  # Update existing driver
            user = driver.user
            user.username = self.cleaned_data['username']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.phone = self.cleaned_data['phone']
            
            # Update password only if provided
            if self.cleaned_data['password']:
                user.set_password(self.cleaned_data['password'])
                
            user.save()
        else:  # Create new driver
            user = CustomUser.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password'] or 'defaultpassword123',
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone'],
                user_type='driver'
            )
        
        driver.user = user
        
        if commit:
            driver.save()
        
        return driver

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = self.instance.user.phone
            self.fields['password'].help_text = "Leave blank to keep the current password"

class VehicleForm(forms.ModelForm):
    """Form for creating/editing vehicles"""
    class Meta:
        model = Vehicle
        fields = ['plate_number', 'model', 'year', 'color', 'seats', 'driver', 'status']
        widgets = {
            'year': forms.NumberInput(attrs={'min': 1900, 'max': 2030}),
            'seats': forms.NumberInput(attrs={'min': 1, 'max': 20}),
        }

class TripForm(forms.ModelForm):
    """Form for creating/editing trips"""
    class Meta:
        model = Trip
        fields = ['user', 'driver', 'vehicle', 'pickup_location', 'dropoff_location', 
                 'pickup_time', 'estimated_arrival', 'fare', 'status']
        widgets = {
            'pickup_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'estimated_arrival': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fare': forms.NumberInput(attrs={'step': '0.01'}),
        }

class UserForm(forms.ModelForm):
    """Form for creating/editing users"""
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15, required=False)  # Make phone optional
    password = forms.CharField(widget=forms.PasswordInput(), required=False,
                               help_text="Leave blank to keep current password")
    
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If this is a new user form, make password required
        if not self.instance.pk:
            self.fields['password'].required = True
            self.fields['password'].help_text = "Enter a secure password"
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # If editing an existing user
        if self.instance.pk:
            # Only validate if email has changed
            if email == self.instance.email:
                return email
                
            # Check if another user has this email
            if CustomUser.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
                raise forms.ValidationError("This email is already registered")
        else:
            # New user - check if email exists
            if CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError("This email is already registered")
        
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # If editing an existing user
        if self.instance.pk:
            # Only validate if username has changed
            if username == self.instance.username:
                return username
                
            # Check if another user has this username
            if CustomUser.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
                raise forms.ValidationError("This username is already taken")
        else:
            # New user - check if username exists
            if CustomUser.objects.filter(username=username).exists():
                raise forms.ValidationError("This username is already taken")
        
        return username
    
    def save(self, commit=True):
        user = self.instance
        user.username = self.cleaned_data['username']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        
        # Handle password
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
            
        # If it's a new user, set the user type
        if not user.pk:
            user.user_type = 'user'
        
        if commit:
            user.save()
        
        return user
# Add this to your ride_management/forms.py file

class LocationForm(forms.ModelForm):
    """Form for creating/editing locations"""
    class Meta:
        model = Location
        fields = ['name', 'address', 'latitude', 'longitude', 'is_airport', 'is_active']
        widgets = {
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
        }



from .models import Location

class LocationForm(forms.ModelForm):
    """Form for creating/editing locations"""
    class Meta:
        model = Location
        fields = ['name', 'address', 'latitude', 'longitude', 'is_airport', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location name'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Latitude (e.g., 8.4834)', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Longitude (e.g., 76.9198)', 'step': '0.000001'}),
            'is_airport': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }