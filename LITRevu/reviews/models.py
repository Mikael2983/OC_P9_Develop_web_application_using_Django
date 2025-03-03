import os
import textwrap
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.utils.timezone import now
from PIL import Image, ImageDraw, ImageFont


class Ticket(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField(max_length=2048)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    picture = models.ImageField(null=True, blank=True, upload_to='')
    time_created = models.DateTimeField(auto_now_add=True)
    answered = models.BooleanField(default=False)

    COVER_SIZE = (469,600)  # Taille standard de l'image finale avec Cover
    IMAGE_SIZE = (300, 460)  # Taille standard de l'image overlay
    OVERLAY_POSITION = (115, 75)  # Décalage (x, y)

    def generate_default_image(self):
        """ Crée une image par défaut avec le titre du ticket """
        default_img_path = os.path.join(settings.MEDIA_ROOT,
                                        f'default_{self.id}.png')

        image = Image.new('RGBA', self.IMAGE_SIZE, color=(
        204, 204, 204, 255))  # Gris clair avec opacité totale
        draw = ImageDraw.Draw(image)

        font_path = os.path.join(settings.BASE_DIR, 'static/fonts/arial.ttf')
        try:
            font = ImageFont.truetype(font_path, 24)
        except IOError:
            font = ImageFont.load_default()

        lines = textwrap.wrap(self.title, width=15)

        line_height = font.getbbox("Test")[3] - font.getbbox("Test")[1]
        total_text_height = len(lines) * line_height
        start_y = (self.IMAGE_SIZE[1] - total_text_height) // 2

        y = start_y
        for line in lines:
            text_width = font.getbbox(line)[2] - font.getbbox(line)[0]
            x = (self.IMAGE_SIZE[0] - text_width) // 2
            draw.text((x, y), line, font=font, fill='black')
            y += line_height

        image.save(default_img_path, format="PNG")

        self.picture.name = f'default_{self.id}.png'
        self.save(update_fields=['picture'])

    def resize_image(self):
        """ Redimensionne et superpose l'image uniquement si une image utilisateur est fournie. """
        if not self.picture:
            self.generate_default_image()
            return

        fond_path = os.path.join(settings.BASE_DIR,
                                 "static/images/couverture.png")
        fond = Image.open(fond_path).convert("RGBA")

        # Charger et redimensionner l'image utilisateur
        overlay = Image.open(self.picture.path).convert(
            "RGBA")  # Supprime la transparence
        overlay_resized = overlay.resize(self.IMAGE_SIZE)

        # Superposer l'image utilisateur sur la couverture
        fond.paste(overlay_resized, self.OVERLAY_POSITION,
                   mask=overlay_resized)

        # Sauvegarde finale en PNG
        fond.save(self.picture.path, format="PNG")

    def save(self, *args, **kwargs):
        """ Sauvegarde le ticket et applique les transformations d'image si besoin. """
        super().save(*args, **kwargs)
        if self.picture and os.path.exists(self.picture.path):
            with Image.open(self.picture.path) as img:
                if img.size != self.COVER_SIZE:
                    self.resize_image()

    def __str__(self):
        return f'{self.title}'


class Review(models.Model):
    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        choices=[(i, f"{i} ★") for i in range(1, 6)])

    headline = models.CharField(max_length=128)
    body = models.CharField(max_length=8192, blank=True)
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.headline}'


class UserFollows(models.Model):
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
