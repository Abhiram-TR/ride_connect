from django import forms
from .models import CustomUser, Driver, Vehicle, Trip, Location 
from django.contrib.auth.forms import UserCreationForm

# ride_management/forms.py
from django import forms
from .models import CustomUser, Driver, Vehicle, Trip

class DriverForm(forms.ModelForm):
    """Form for creating/editing drivers"""
    username = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    
    class Meta:
        model = Driver
        fields = ['license_number', 'license_expiry', 'status']
        widgets = {
            'license_expiry': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def save(self, commit=True):
        driver = super().save(commit=False)
        
        # Create or update user
        if driver.pk:  # Update existing
            user = driver.user
            user.username = self.cleaned_data['username']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.phone = self.cleaned_data['phone']
            if self.cleaned_data['password']:
                user.set_password(self.cleaned_data['password'])
        else:  # Create new
            user = CustomUser.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone'],
                password=self.cleaned_data['password'] or 'defaultpassword123',
                user_type='driver'
            )
        
        user.save()
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
    phone = forms.CharField(max_length=15)
    password1 = forms.CharField(widget=forms.PasswordInput(), label='Password', required=False)
    password2 = forms.CharField(widget=forms.PasswordInput(), label='Confirm Password', required=False)
    password = forms.CharField(widget=forms.PasswordInput(), label='New Password', required=False)
    
    class Meta:
        model = CustomUser
        fields = []  # We'll handle fields manually
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # Edit form
            self.fields['username'].initial = self.instance.username
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            self.fields['email'].initial = self.instance.email
            self.fields['phone'].initial = self.instance.phone
            # Remove password2 for edit form
            del self.fields['password2']
        else:  # Create form
            # Remove password for create form
            del self.fields['password']
            self.fields['password1'].required = True
            self.fields['password2'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if not self.instance.pk:  # Create form
            if password1 and password2 and password1 != password2:
                raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = self.instance
        
        if not user.pk:  # New user
            user = CustomUser.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password1'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone'],
                user_type='user'
            )
        else:  # Existing user
            user.username = self.cleaned_data['username']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.phone = self.cleaned_data['phone']
            
            if self.cleaned_data.get('password'):
                user.set_password(self.cleaned_data['password'])
            
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