from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
       Custom user model extending Django's AbstractUser.

       This model adds a profile photo field to the default Django user model.

       Attributes:
           profile_photo (ImageField): An image field for storing the user's profile picture.
    """
    profile_photo = models.ImageField(verbose_name='Photo de profil')


