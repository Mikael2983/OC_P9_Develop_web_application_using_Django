from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from authentification.models import User
from .forms import UserUpdateForm, SignupForm


class CustomLoginView(LoginView):
    """
    Custom login view extending Django's LoginView.

    This view handles user authentication and redirects the user
    to the 'flux' page upon successful login.
    """

    def get_success_url(self, **kwargs):
        return reverse_lazy('flux')


class CustomSignUpView(CreateView):
    form_class = SignupForm
    success_url = reverse_lazy("login")


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "authentification/account.html"
    success_url = reverse_lazy("flux")

    def get_object(self):
        """Récupère l'utilisateur actuellement connecté."""
        return self.request.user
