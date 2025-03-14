from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
       Custom user model extending Django's AbstractUser.

       This model adds a profile photo field to the default Django user model.

       Attributes:
           profile_photo: An imagefield for storing the user's profile picture.
    """

    email = models.EmailField(unique=True)
