from django.shortcuts import render


def accueil(requests):
    return render(requests, 'reviews/accueil.html')


def connexion(requests):
    return render( requests, 'reviews/connexion.html')
