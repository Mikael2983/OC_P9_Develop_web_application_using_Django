from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms

from authentification.models import User


class SignupForm(UserCreationForm):
    """
    Custom user signup form extending Django's UserCreationForm.

    This form is used for user registration, allowing users to create
    an account with only a username.

    Attributes:
        model (User): The custom user model retrieved with `get_user_model()`.
        fields (list): The fields to be included in the form (only 'username').
    """
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'email']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]
