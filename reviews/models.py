import os
import textwrap
from django.conf import settings
from django.db import models

from PIL import Image, ImageDraw, ImageFont


class Ticket(models.Model):
    """
       Model representing a support or review ticket.

       This model stores user-generated tickets with an optional image.
       If no image is provided, a default one is generated with the
       ticket's title. Uploaded images are converted to WebP format and
       resized for optimization.

       Attributes:
           title (CharField): The title of the ticket.
           description (TextField): A detailed description of the ticket.
           user (ForeignKey): The user who created the ticket.
           picture (ImageField): An optional image associated with the ticket.
           time_created (DateTimeField): The creation timestamp of the ticket
           IMAGE_SIZE (tuple): The dimensions for ticket images (141x180).

       Methods:
           save(*args, **kwargs):
               Overrides the default save method to handle image conversion and
                generation.
           _process_uploaded_image():
               Converts images to WebP format and resizes them if needed.
           _generate_default_image():
               Creates a default WebP image with the ticket title.
           __str__():
               Returns the ticket title as its string representation.
       """

    title = models.CharField(max_length=128)
    description = models.TextField(max_length=2048)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE
                             )
    picture = models.ImageField(null=True, blank=True, upload_to='')
    time_created = models.DateTimeField(auto_now_add=True)

    IMAGE_SIZE = (141, 180)

    def save(self, *args, **kwargs):
        """
        Sauvegarde l'objet et gère les images (conversion et génération).
        """

        super().save(*args, **kwargs)

        if self.picture:
            with Image.open(self.picture.path) as img:
                # Vérifier si l'image est déjà en WebP et à la bonne taille
                is_webp = self.picture.name.lower().endswith(".webp")
                correct_size = img.size == self.IMAGE_SIZE

                if not (is_webp and correct_size):
                    self._process_uploaded_image()

        elif not self.picture:
            self._generate_default_image()

    def _process_uploaded_image(self):
        """
        Converts to WebP and resizes the image only if necessary.
        """
        img_path = self.picture.path
        webp_path = os.path.splitext(img_path)[0] + ".webp"

        with Image.open(img_path) as img:
            img = img.convert("RGBA").resize(self.IMAGE_SIZE)
            img.save(webp_path, "WEBP", lossless=True)

        self.picture.name = f'{os.path.basename(webp_path)}'
        self.save(update_fields=["picture"])

    def _generate_default_image(self):
        """
        Creates a default WebP image with the ticket title.
        """
        if not self.id:
            return  # évite les erreurs avant la première sauvegarde

        webp_path = os.path.join(settings.MEDIA_ROOT,
                                 f'default_{self.id}.webp')

        image = Image.new("RGBA",
                          self.IMAGE_SIZE,
                          (204, 204, 204, 255)
                          )
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()

        lines = textwrap.wrap(self.title, width=15)
        y = (self.IMAGE_SIZE[1] - len(
            lines) * 12) // 2  # Centrage vertical

        for line in lines:
            x = (self.IMAGE_SIZE[0] - len(
                line) * 6) // 2  # Approximation centrage horizontal
            draw.text((x, y), line, font=font, fill="black")
            y += 12

        image.save(webp_path, "WEBP", lossless=True)
        self.picture.name = f'default_{self.id}.webp'
        self.save(
            update_fields=["picture"])

    def __str__(self):
        return self.title


class Review(models.Model):
    """
   Model representing a user review for a ticket.

   This model stores user-generated reviews associated with a specific ticket.
   Each review includes a rating, headline, and optional body text.

   Attributes:
       ticket (ForeignKey): The ticket being reviewed, with cascading deletion.
       rating (PositiveSmallIntegerField): The rating given by the user,
                                           ranging from 1 to 5 stars.
       headline (CharField): A brief summary of the review.
       body (CharField): The detailed content of the review.
       user (ForeignKey): The user who created the review.
       time_created (DateTimeField): The review creation timestamp.

   Methods:
       __str__():
           Returns the headline of the review as its string representation.
   """

    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        choices=[(i, f"{i} ★") for i in range(1, 6)])

    headline = models.CharField(max_length=128)
    body = models.TextField(max_length=8192, blank=True)
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.headline}'


class UserFollows(models.Model):
    """
    Model representing a user following another user.

    This model stores relationships between users to track who follows whom.
    It also includes a flag to indicate if a user has been banned from
    interacting.

    Attributes:
        user (ForeignKey): The user who is following another user.
        followed_user (ForeignKey): The user being followed.
        banned (BooleanField): Indicates if the followed user is restricted
                               from interacting with the follower.

    Meta:
        unique_together (tuple): Ensures that a user cannot follow the same
        user multiple times.

    """
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='following')
    followed_user = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                      on_delete=models.CASCADE,
                                      related_name='followers')
    banned = models.BooleanField(default=False)

    class Meta:
        # ensures we don't get multiple UserFollows instances
        # for unique user-user_followed pairs
        unique_together = ('user', 'followed_user')
