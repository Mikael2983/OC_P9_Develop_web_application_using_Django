from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.urls import reverse
from . import forms
from authentification.models import User


class CustomLoginView(LoginView):
    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return redirect(reverse(
            'flux',
            ))


def signup_page(request):
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
    if request.method == 'POST':
        print('post')
        logout(request)
        return redirect(reverse(
                'login'))
    return render(request,
                  'authentification/logout.html'
                  )


def reset_password(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        if not username:
            return render(request, 'authentification/reset_password.html', {'error': "Veuillez entrer un nom d'utilisateur."})

        user = User.objects.filter(username=username).first()

        if not user:
            return render(request, 'authentification/reset_password.html', {'error': "Utilisateur introuvable"})

        request.session['reset_user_id'] = user.id
        return redirect('set_new_password')

    return render(request, 'authentification/reset_password.html')


def set_new_password(request):
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
    return render(request, 'authentification/password_reset_done.html')
