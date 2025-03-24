from django import forms

from authentification.models import User
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
        labels = {
            'title': "Titre",
            'description': "Description",
            'picture': "Image (optionnelle)",
        }


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
        label="Titre",
        max_length=150,
    )
    rate_choices = ((i, i * '★') for i in range(1, 6))
    rating = forms.ChoiceField(choices=rate_choices,
                               widget=forms.RadioSelect(),
                               label="Note"
                               )

    class Meta:
        model = Review
        fields = ['headline', 'rating', 'body']
        labels = {
            'body': "Commentaire"
        }


class FollowUserForm(forms.Form):
    """
    Form for following another user.

    This form allows users to search for and follow another user by selecting
    their username from a dropdown list.

    Attributes:
        current_user (User): The user who is initiating the follow action.
    """

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user',
                                       None)  # Extract user from kwargs
        super().__init__(*args, **kwargs)
        self.fields['user'] = forms.ModelChoiceField(
            queryset=self.filter_users(),
            label="Sélectionner un utilisateur",
            widget=forms.Select(attrs={'class': 'form-control'}),
        )

    def filter_users(self):
        """
        Selects users to be displayed in the dropdown menu.

        Excludes from the list:
            - Users that the current user is already following.
            - Users who have blocked the current user.

        Returns:
            QuerySet: A list of users that the current user can follow, excluding
            admin users and the current user.
        """
        following_users = User.objects.filter(
            followers__user=self.current_user
                                           )
        banning_users = User.objects.filter(
            following__followed_user=self.current_user,
            following__banned=True)

        excluded_users = following_users.union(
            banning_users).values_list('id', flat=True)

        user_to_follow = (
            User.objects.all().exclude(username='admin')
            .exclude(username=self.current_user)
            .exclude(id__in=excluded_users)
        )

        return user_to_follow
