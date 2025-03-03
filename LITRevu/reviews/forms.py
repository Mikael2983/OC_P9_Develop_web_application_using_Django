from django import forms
from reviews.models import Ticket, Review


class TicketForm(forms.ModelForm):


    class Meta:
        model = Ticket
        fields = ['title', 'description', 'picture']


class ReviewForm(forms.ModelForm):
    headline = forms.CharField(
        label="titre",
        max_length=150,
    )
    rate_choices = ((i, i*f"★")for i in range(1, 6))
    rating = forms.ChoiceField(choices=rate_choices, widget=forms.RadioSelect())

    class Meta:
        model = Review
        fields = ['headline', 'body', 'rating']


class FollowUserForm(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        widget=forms.TextInput(
            attrs={'placeholder': 'Entrez un nom d’utilisateur'})
    )
