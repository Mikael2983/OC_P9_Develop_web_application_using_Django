from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.urls import reverse
from . import forms
from authentification.models import User


class CustomLoginView(LoginView):
    """
    Custom login view extending Django's LoginView.

    This view handles user authentication and redirects the user
    to the 'flux' page upon successful login.
    """
    def form_valid(self, form: dict):
        """
        Log in the user if the form is valid and redirect to the 'flux' page.

        This method retrieves the authenticated user from the form, logs them in,
        and redirects them to the main content page.

        Args:
            form (AuthenticationForm): The authentication form containing
                                       the validated user credentials.

        Returns:
            HttpResponseRedirect: A redirect to the 'flux' page upon successful login.
        """
        user = form.get_user()
        login(self.request, user)
        return redirect(reverse(
            'flux',
            ))


def signup_page(request):
    """
    Display the signup form and handle user registration.

    This view handles both the display of the signup form and the
    processing of the form submission. If the request method is GET,
    it renders the empty signup form. If the request method is POST,
    it validates the submitted form data. If valid, a new user is
    created, logged in, and redirected to the 'flux' page.

    Args:
        request (HttpRequest): The request object containing
                               metadata about the request.

    Returns:
        HttpResponse: A rendered signup page with the form if the
                      request is GET or if the form is invalid.
        HttpResponseRedirect: A redirect to the 'flux' page upon
                              successful signup.
    """
    form = forms.SignupForm()
    if request.method == 'POST':
        form = forms.SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse(
                'flux',
                ))
    return render(request,
                  'authentification/signup.html',
                  {'form': form}
                  )


def custom_logout(request):
    """
    Handle user logout using the POST method.

    This view ensures that the user is logged out only via a POST request
    to prevent accidental logouts via GET requests. If the request method
    is POST, the user is logged out, and they are redirected to the
    login page. Otherwise, a logout confirmation page is displayed.

    Args:
        request (HttpRequest): The request object containing metadata
                               about the request.

    Returns:
        HttpResponseRedirect: A redirect to the 'login' page if the
                              request method is POST.
        HttpResponse: A rendered logout confirmation page if the
                      request method is not POST.
    """

    if request.method == 'POST':
        print('post')
        logout(request)
        return redirect(reverse(
                'login'))
    return render(request,
                  'authentification/logout.html'
                  )


def reset_password(request):
    """
    Display the password reset form and handle user identification.

    This view renders a form where a user can enter their username to initiate
    the password reset process. If the request method is POST, it validates the
    provided username, checks if the user exists in the database, and stores
    their user ID in the session before redirecting to the password reset page.

    Args:
        request (HttpRequest): The request object containing metadata
                               about the request.

    Returns:
        HttpResponseRedirect: A redirect to the 'set_new_password' page
                              if the username is valid.
        HttpResponse: A rendered reset password page with an error message
                      if the username is missing or invalid.
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        if not username:
            return render(request,
                          'authentification/reset_password.html',
                          {'error': "Veuillez entrer un nom d'utilisateur."})

        user = User.objects.filter(username=username).first()

        if not user:
            return render(request,
                          'authentification/reset_password.html',
                          {'error': "Utilisateur introuvable"})

        request.session['reset_user_id'] = user.id
        return redirect('set_new_password')

    return render(request, 'authentification/reset_password.html')


def set_new_password(request):
    """
    Display the new password form and handle password reset.

    This view allows a user to set a new password after verifying their identity
    through a prior step. If the user ID is not found in the session, they are
    redirected to the reset password page. If the request method is POST, it
    validates the new password and updates the user's password if both fields match.

    Args:
        request (HttpRequest): The request object containing metadata
                               about the request.

    Returns:
        HttpResponseRedirect: A redirect to the 'password_reset_done' page
                              if the password is successfully changed.
        HttpResponseRedirect: A redirect to 'reset_password' if no user ID is found
                              in the session.
        HttpResponse: A rendered set new password page with an error message
                      if the passwords do not match.
    """
    user_id = request.session.get('reset_user_id')

    if not user_id:  # Si pas d'utilisateur en session, retour à la page de réinitialisation
        return redirect('reset_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            user = User.objects.get(id=user_id)
            user.password = make_password(new_password)
            user.save()
            del request.session[
                'reset_user_id']  # Supprime l’ID utilisateur de la session
            return redirect('password_reset_done')
        else:
            return render(request, 'authentification/set_new_password.html',
                          {'error': "Les mots de passe ne correspondent pas."})

    return render(request, 'authentification/set_new_password.html')


def password_reset_done(request):
    """
    Display the password reset success confirmation page.

    This view renders a confirmation page informing the user
    that their password has been successfully changed.

    Args:
        request (HttpRequest): The request object containing metadata
                               about the request.

    Returns:
        HttpResponse: A rendered password reset confirmation page.
    """
    return render(request, 'authentification/password_reset_done.html')
