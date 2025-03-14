import os
import django
from django.core.mail import send_mail

# Définir les settings Django manuellement
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LITRevu.settings")
django.setup()


send_mail(
    "Test Email",
    "Ceci est un test d'envoi d'email avec EmailBackend.",
    "noreply@example.com",  # Expéditeur
    ["ton_email@example.com"],  # Destinataire
    fail_silently=False,
)
