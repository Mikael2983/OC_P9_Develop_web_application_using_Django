from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
       Custom user model extending Django's AbstractUser.

       This model adds a profile photo field to the default Django user model.

       Attributes:
           email: An emailfield for storing the user's email.
    """

    email = models.EmailField(unique=True)
