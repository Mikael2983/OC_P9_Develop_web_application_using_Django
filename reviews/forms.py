from django import forms
from reviews.models import Ticket, Review


class TicketForm(forms.ModelForm):
    """
    Form for creating or updating a ticket.

    This form allows users to submit a ticket with a title, description,
    and an optional image.

    Meta:
        model (Ticket): The model associated with this form.
        fields (list): Specifies the fields to include in the form.
    """

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'picture']


class ReviewForm(forms.ModelForm):
    """
    Form for creating or updating a review.

    This form allows users to submit a review with a headline, a body
    and a rating.

    Meta:
        model (review): The model associated with this form.
        fields (list): Specifies the fields to include in the form.
    """
    headline = forms.CharField(
        label="titre",
        max_length=150,
    )
    rate_choices = ((i, i*'★')for i in range(1, 6))
    rating = forms.ChoiceField(choices=rate_choices,
                               widget=forms.RadioSelect()
                               )

    class Meta:
        model = Review
        fields = ['headline', 'body', 'rating']


class FollowUserForm(forms.Form):
    """
    Form for following another user.

    This form allows users to search for and follow another user by entering
    their username.

    Attributes:
        username (CharField): A text input field for the username,
                              with a maximum length of 150 characters.
    """
    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        widget=forms.TextInput(
            attrs={'placeholder': 'Entrez un nom d’utilisateur'})
    )
