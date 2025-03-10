from itertools import chain

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from authentification.models import User
from reviews.models import Review, Ticket, UserFollows
from reviews.forms import ReviewForm, TicketForm, FollowUserForm


@login_required
def flux(request):
    """
    Display the main feed with user reviews and tickets.

    This view retrieves and paginates reviews and tickets from the user and
    the users he follows, while excluding content from banned users.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The feed page with paginated reviews and tickets.
    """
    # list of users who have banned the user
    banning_users = User.objects.filter(followers__user=request.user,
                                        followers__banned=True)
    # list of users banned by the user
    banned_users = User.objects.filter(following__followed_user=request.user,
                                       following__banned=True)
    # list of all users followed by the user
    following_users = UserFollows.objects.filter(
        user=request.user).values_list('followed_user', flat=True)

    users = chain([request.user], following_users)
    list_users = list(users)

    # list of reviews of the user and those he follows
    reviews = Review.objects.filter(
        Q(user__in=list_users) |
        Q(ticket__in=Ticket.objects.filter(user__in=list_users))
    ).exclude(ticket__user__in=banned_users)

    # list of tickets of the user and those he follows
    tickets = Ticket.objects.filter(user__in=list_users)

    reviews_and_tickets = sorted(
        chain(reviews, tickets),
        key=lambda instance: instance.time_created,
        reverse=True
    )

    paginator = Paginator(reviews_and_tickets, 6)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'banning_users': banning_users
    }
    return render(request,
                  'reviews/flux.html',
                  context)


@login_required
def create_review(request):
    """
    Handle the creation of a review along with an associated ticket.

    This view processes a POST request containing form data for both a
    `TicketForm` and a `ReviewForm`. If both forms are valid, a new ticket and
    a new review are created and linked to the requesting user.
    The ticket is marked as answered.

    Args:
        request (HttpRequest): The HTTP request object containing user data and
         form inputs.

    Returns:
        HttpResponse: The appropriate response after processing the forms.
    """
    if request.method == "POST":
        ticket_form = TicketForm(request.POST, request.FILES)
        review_form = ReviewForm(request.POST)

        if ticket_form.is_valid() and review_form.is_valid():
            ticket = ticket_form.save(commit=False)
            ticket.user = request.user

            review = review_form.save(commit=False)
            review.user = request.user
            review.ticket = ticket
            ticket.answered = True

            ticket.save()
            review.save()

            return redirect('flux')

    else:
        ticket_form = TicketForm()
        review_form = ReviewForm()

    context = {
        'ticket_form': ticket_form,
        'review_form': review_form
    }
    return render(request, 'reviews/create_review.html', context)


@login_required
def modify_review(request, review_id):
    """
    Handle the modification of an existing review.

    This view retrieves a review by its ID and ensures that the requesting
    user is the owner of the review. If the user is not the owner, they are
    redirected to the 'flux' page. If the request method is POST and the form
    is valid, the review is updated and the user is redirected to 'flux'.
    Otherwise, the form is displayed for editing.

    Args:
        request (HttpRequest): The HTTP request object containing user data and
                                form inputs.
        review_id (int): The ID of the review to be modified.

    Returns:
        HttpResponse: Renders the review modification page with the form,
                      or redirects to 'flux' if unauthorized or upon
                      successful submission.
    """
    review = Review.objects.get(id=review_id)
    if request.user != review.user:
        return redirect(reverse('flux'))

    ticket = Ticket.objects.get(id=review.ticket_id)
    if request.method == 'POST':
        review_form = ReviewForm(request.POST, instance=review)
        if review_form.is_valid():
            review_form.save()
            return redirect(reverse('flux'))
    else:
        review_form = ReviewForm(instance=review)

    return render(request,
                  'reviews/modify_review.html',
                  {'review_form': review_form, 'review': review,
                   'ticket': ticket})


@login_required
def delete_review(request, review_id):
    """
    Handle the deletion of a review.

    This view allows a user to delete their own review. If the requesting user
    is not the owner of the review, he is redirected to the 'flux' page.
    If the request method is POST, the review is deleted, and the user is
    redirected to the 'user_posts' page. Otherwise, a confirmation page
    is displayed.

    Args:
        request (HttpRequest): The HTTP request object containing user data.
        review_id (int): The ID of the review to be deleted.

    Returns:
        HttpResponse: Renders the review deletion confirmation page,
                      or redirects to 'flux' if unauthorized, or 'user_posts'
                      upon deletion.
    """
    review = Review.objects.get(id=review_id)
    ticket = Ticket.objects.get(id=review.ticket)

    if request.user != review.user:
        return redirect(reverse('flux'))

    if request.method == 'POST':
        ticket.answered = False
        review.delete()
        return redirect(reverse('user_posts'))

    return render(request,
                  'reviews/delete_review.html',
                  {'review': review})


@login_required
def create_ticket(request):
    """
    Handle the creation of a new ticket.

    This view processes a POST request containing form data for creating a new
    ticket. If the form is valid, a ticket is created and associated with the
    requesting user. The ticket's creation timestamp is set to the current
    time. Upon success, the user is redirected to the 'flux' page. If the
    request method is GET, an empty form is displayed for the user.

    Args:
        request (HttpRequest): The HTTP request object containing user data and
                                form inputs.

    Returns:
        HttpResponse: Renders the ticket creation page with the form,
                      or redirects to 'flux' upon successful submission.
    """
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.time_created = now()
            ticket.save()
            return redirect(reverse('flux'), {'form': form})
        else:
            print(form.errors)
    else:
        form = TicketForm()

    return render(request,
                  'reviews/create_ticket.html',
                  {'form': form})


@login_required
def user_posts(request):
    """
    Display a list of the user's reviews and tickets.

    This view retrieves all reviews and tickets created by the requesting user.
    It includes:
      - Reviews authored by the user.
      - Reviews on tickets created by the user.
      - All tickets created by the user.

    The reviews and tickets are combined, sorted in descending order by their
    creation timestamp, and displayed in the 'user_posts.html' template.

    Args:
        request (HttpRequest): The HTTP request object containing user data.

    Returns:
        HttpResponse: Renders the 'user_posts.html' template with the sorted
                      reviews and tickets.
    """
    reviews = Review.objects.filter(
        Q(user=request.user) |
        Q(ticket__user=request.user)
    ).distinct()

    tickets = Ticket.objects.filter(user=request.user)

    reviews_and_tickets = sorted(
        chain(reviews, tickets),
        key=lambda instance: instance.time_created,
        reverse=True
    )

    return render(request,
                  'reviews/user_posts.html',
                  {'reviews_and_tickets': reviews_and_tickets})


@login_required
def modify_ticket(request, ticket_id):
    """
    Handle the modification of an existing ticket.

    This view allows a user to modify their own ticket. If the requesting user
    is not the owner of the ticket, they are redirected to the 'flux' page.
    If the form is valid, the ticket is updated and the user is redirected to
    the 'user_posts' page. Otherwise, the form is displayed pre-filled with
    the existing ticket data.

    Args:
        request (HttpRequest): The HTTP request object containing user data and
         form inputs.
        ticket_id (int): The ID of the ticket to be modified.

    Returns:
        HttpResponse: Renders the ticket modification page with the form,
                      or redirects to 'flux' if unauthorized, or 'user_posts'
                      upon success.
    """
    ticket = Ticket.objects.get(id=ticket_id)

    if request.user != ticket.user:
        return redirect(reverse('flux'))

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect(reverse('user_posts'))
    else:
        form = TicketForm(instance=ticket)

    return render(request,
                  'reviews/modify_ticket.html',
                  {'form': form, 'ticket': ticket})


def answer_ticket(request, ticket_id):
    """
    Handle the creation of a review in response to a ticket.

    This view allows a user to respond to a ticket by submitting a review.
    If the request method is POST and the review form is valid, the review is
    associated with the ticket, and the ticket is marked as answered. The user
    is then redirected to the 'flux' page. If the request method is GET, an
    empty review form is displayed.

    Args:
        request (HttpRequest): The HTTP request object containing user data and
         form inputs.
        ticket_id (int): The ticket ID being answered.

    Returns:
        HttpResponse: Renders the review submission page with the form and
                      ticket details or redirects to 'flux' upon successful
                      submission.
    """
    if request.method == "POST":
        ticket = Ticket.objects.get(id=ticket_id)
        review_form = ReviewForm(request.POST, instance=ticket)

        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.user = request.user
            review.ticket = ticket  # Associer la critique au ticket créé
            ticket.answered = True

            ticket.save()
            review.save()

            return redirect('flux')  # Redirection après la soumission

    else:
        review_form = ReviewForm()
        ticket = Ticket.objects.get(id=ticket_id)
    context = {
        'ticket': ticket,
        'review_form': review_form
    }
    return render(request, 'reviews/answer_review.html', context)


@login_required
def delete_ticket(request, ticket_id):
    """
    Handle the deletion of a ticket.

    This view allows a user to delete their own ticket. If the requesting user
    is not the owner of the ticket, they are redirected to the 'flux' page.
    If the request method is POST, the ticket is deleted, and the user is
    redirected to the 'user_tickets' page. Otherwise, a confirmation page
    is displayed.

    Args:
        request (HttpRequest): The HTTP request object containing user data.
        ticket_id (int): The ID of the ticket to be deleted.

    Returns:
        HttpResponse: Renders the ticket deletion confirmation page,
                      or redirects to 'flux' if unauthorized, or 'user_tickets'
                      upon deletion.
    """
    ticket = Ticket.objects.get(id=ticket_id)

    if request.user != ticket.user:
        return redirect(reverse('flux'))

    if request.method == 'POST':
        ticket.delete()
        return redirect(reverse('user_posts'))

    return render(request,
                  'reviews/delete_ticket.html',
                  {'ticket': ticket})


@login_required
def follow(request):
    """
   Handle user follow and unfollow actions while managing bans.

   This view allows users to follow other users, ensuring that:
     - They cannot follow themselves.
     - They cannot follow a user they are already following.
     - They cannot follow a user who has blocked them.
     - The form prevents following non-existent users.

   It also retrieves:
     - Users who have blocked the requesting user.
     - Users that the requesting user has blocked.
     - Users following the requesting user.
     - Users the requesting user is following, excluding those who have blocked
      them.

   Args:
       request (HttpRequest): The HTTP request object containing user data and
        form inputs.

   Returns:
       HttpResponse: Renders the 'follow.html' template with the form and lists
                     of users.
                     Redirects to 'follow' upon successful submission or an
                     error.
   """
    banned_users = User.objects.filter(following__followed_user=request.user,
                                       following__banned=True)

    banning_users = User.objects.filter(followers__user=request.user,
                                        followers__banned=True)

    followers_users = User.objects.filter(
        following__followed_user=request.user)

    following_users = User.objects.filter(
        followers__user=request.user).exclude(id__in=banned_users)

    if request.method == "POST":
        form = FollowUserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if not User.objects.filter(username=username).exists():
                messages.error(request, "cet utilisateur n'existe pas")
            else:
                user_to_follow = User.objects.get(username=username)

                if UserFollows.objects.filter(
                        user=user_to_follow,
                        followed_user=request.user
                ).exists():

                    user_relation = get_object_or_404(
                        UserFollows,
                        user=user_to_follow,
                        followed_user=request.user
                    )
                    if user_relation.banned:
                        messages.error(request,
                                       "cet utilisateur vous a bloqué")
                        return redirect('follow')

                if user_to_follow == request.user:
                    messages.error(
                        request,
                        "Vous ne pouvez pas vous suivre vous-même.")

                elif UserFollows.objects.filter(
                        user=request.user,
                        followed_user=user_to_follow
                ).exists():

                    messages.error(request,
                                   "Vous suivez déjà cet utilisateur.")

                else:
                    UserFollows.objects.create(user=request.user,
                                               followed_user=user_to_follow)
                    return redirect(
                        'follow')

    else:
        form = FollowUserForm()

    return render(request,
                  'reviews/follow.html',
                  {
                      'form': form,
                      'followers_users': followers_users,
                      'following_users': following_users,
                      'banned_users': banned_users,
                      'banning_users': banning_users,
                  })


@login_required
def unfollow(request, user_id):
    """
    Handle the unfollowing of a user.

    This view allows the requesting user to unfollow another user.
    If the specified user does not exist, a 404 error is raised.
    The follow relationship is deleted if it exists, and the user is
    redirected to the 'follow' page.

    Args:
        request (HttpRequest): The HTTP request object containing user data.
        user_id (int): The ID of the user to unfollow.

    Returns:
        HttpResponseRedirect: Redirects to the 'follow' page after unfollowing.
    """
    user_to_unfollow = get_object_or_404(User, id=user_id)
    follow_relation = UserFollows.objects.filter(
        user=request.user,
        followed_user=user_to_unfollow
    )
    follow_relation.delete()
    return redirect('follow')


@login_required
def unsubscribe_followers(request, user_id):
    """
        Remove a follower from the requesting user's followers list.

        This view allows the requesting user to remove a specific follower.
        If the specified user does not exist, a 404 error is raised.
        If a follow relationship exists, it is deleted, and the user is
        redirected to the 'follow' page.

        Args:
            request (HttpRequest): The request object containing user data.
            user_id (int): The ID of the follower to remove.

        Returns:
            HttpResponseRedirect: Redirects to the 'follow' page after removal.
        """
    user_to_unsubscribe = get_object_or_404(User, id=user_id)

    follow_relation = UserFollows.objects.filter(user=user_to_unsubscribe,
                                                 followed_user=request.user)
    follow_relation.delete()

    return redirect('follow')


@login_required
def ban_followers(request, user_id):
    """
    Restrict a follower from interacting with the user's content.

    This view marks a follower as banned, preventing them from interacting with
    the user's content. It retrieves the follower relationship and updates
    its status.

    Args:
        request (HttpRequest): The HTTP request object.
        user_id (int): The ID of the user to ban.

    Returns:
        HttpResponseRedirect: A redirect to the 'follow' page.
    """
    user_to_ban = get_object_or_404(User, id=user_id)
    follow_relation = get_object_or_404(UserFollows,
                                        user=user_to_ban,
                                        followed_user=request.user)
    follow_relation.banned = True
    follow_relation.save()
    return redirect('follow')


@login_required
def unban_followers(request, user_id):
    """
    Remove interaction restrictions from a previously banned follower.

    This view allows a previously restricted follower to interact again
    with the user's content. It updates the follower relationship to lift
    the restriction.

    Args:
        request (HttpRequest): The HTTP request object.
        user_id (int): The ID of the user to unban.

    Returns:
        HttpResponseRedirect: A redirect to the 'follow' page after updating
                              the status.
    """
    user_to_ban = get_object_or_404(User, id=user_id)
    follow_relation = get_object_or_404(UserFollows,
                                        user=user_to_ban,
                                        followed_user=request.user)
    follow_relation.banned = False
    follow_relation.save()
    return redirect('follow')
