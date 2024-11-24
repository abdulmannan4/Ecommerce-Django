from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django.core.exceptions import ValidationError

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    username = forms.CharField(max_length=30, label='Username', required=True)
    tc = forms.BooleanField(required=True, label='I agree to the terms and conditions')

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2', 'tc')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit.")
        if not any(char.isalpha() for char in password):
            raise ValidationError("Password must contain at least one letter.")
        return password
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    remember_me = forms.BooleanField(required=False, label="Remember Me")

    class Meta:
        model = User
        fields = ('email', 'password')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is not registered.")
        return email
from .models import Customer,ShippingAddress  # Adjust the import based on your app structure

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name','last_name','phone_number', 'address', 'city', 'postal_code', 'country']
        widgets = {
            
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
            'address': forms.TextInput(attrs={'placeholder': 'Enter your address'}),
            'city': forms.TextInput(attrs={'placeholder': 'Enter your city'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Enter your postal code'}),
            'country': forms.TextInput(attrs={'placeholder': 'Enter your country'}),
        }
class ShippingForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['address', 'city', 'postal_code', 'country']
        widgets = {
            'address': forms.TextInput(attrs={'placeholder': 'Enter your address'}),
            'city': forms.TextInput(attrs={'placeholder': 'Enter your city'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Enter your postal code'}),
            'country': forms.TextInput(attrs={'placeholder': 'Enter your country'}),
        }
