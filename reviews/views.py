from itertools import chain

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet

from authentification.models import User

from .models import Review, Ticket, UserFollows
from .forms import ReviewForm, TicketForm, FollowUserForm


def get_banning_users(user: User) -> QuerySet:
    """
    Retrieves users who have banned the given user.

    Args:
        user (User): The user for whom we want to find blockers.

    Returns:
        QuerySet: A list of users who have banned the given user.
    """
    return User.objects.filter(
        following__followed_user=user,
        following__banned=True
    )


def get_banned_users(user: User) -> QuerySet:
    """
    Retrieves the users that the given user has banned.

    Args:
        user (User): The user who has banned other users.

    Returns:
        QuerySet: A list of users who have been banned by the given user.
    """
    return User.objects.filter(
        followers__user=user,
        followers__banned=True
    )


def get_followers(user: User) -> QuerySet:
    """
    Retrieves the users who follow the given user, excluding those who have
    banned him.

    Args:
        user (User): The user whose followers we want to retrieve.

    Returns:
        QuerySet: A list of users following the given user, excluding those who
         have banned him.
    """
    banning_users = get_banning_users(user)
    return User.objects.filter(
        following__followed_user=user
    ).exclude(id__in=banning_users)


def get_followings(user: User) -> QuerySet:
    """
    those that the user follows less those who have banned him and those that
    the user has banned
    """
    banning_users = get_banning_users(user)
    banned_users = get_banned_users(user)
    return User.objects.filter(
        followers__user=user).exclude(
        id__in=banning_users).exclude(
        id__in=banned_users)


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
        form = TicketForm(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect(reverse('flux'))
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
        review_form = ReviewForm(request.POST)

        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.user = request.user
            review.ticket = ticket

            review.save()

            return redirect('flux')

    else:
        review_form = ReviewForm()
        ticket = Ticket.objects.get(id=ticket_id)

    context = {
        'ticket': ticket,
        'review_form': review_form
    }
    return render(request, 'reviews/answer_ticket.html', context)


@login_required
def delete_ticket(request, ticket_id):
    """
    Handle the deletion of a ticket.

    This view allows a user to delete their own ticket. If the requesting user
    is not the owner of the ticket, they are redirected to the 'flux' page.
    If the request method is POST, the ticket is deleted, and the user is
    redirected to the 'flux' page. Otherwise, a confirmation page
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
        return redirect(reverse('flux'))

    return render(request,
                  'reviews/delete_ticket.html',
                  {'ticket': ticket})


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
                  {'review_form': review_form,
                   'review': review,
                   'ticket': ticket})


@login_required
def delete_review(request, review_id):
    """
    Handle the deletion of a review.

    This view allows a user to delete their own review. If the requesting user
    is not the owner of the review, he is redirected to the 'flux' page.
    If the request method is POST, the review is deleted, and the user is
    redirected to the 'flux' page. Otherwise, a confirmation page
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

    if request.user != review.user:
        return redirect(reverse('flux'))

    if request.method == 'POST':
        review.delete()
        return redirect(reverse('flux'))

    return render(request,
                  'reviews/delete_review.html',
                  {'review': review})


@login_required
def flux(request):
    """
    Display the main feed with the reviews and the tickets of the user and his
    following users.

    This view retrieves and paginates reviews and tickets from the user and
    the users he follows, while excluding content from banned users.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The feed page with paginated reviews and tickets.
    """

    banning_users = get_banning_users(request.user)

    banned_users = get_banned_users(request.user)

    following_users = get_followings(request.user)

    users = chain([request.user], following_users)
    list_users = list(users)

    # list of user tickets that have had a review
    user_answered_tickets = Ticket.objects.filter(review__isnull=False,
                                                  user=request.user).distinct()

    # list of tickets that have a user review
    user_review_tickets = Ticket.objects.filter(
        review__user=request.user).distinct()

    # list of reviews of the user and those he follows
    reviews = (Review.objects.select_related("user", "ticket").filter(
        Q(user__in=list_users) |
        Q(ticket__user__in=list_users))
               .exclude(user__in=banned_users)
               .exclude(ticket__user__in=banned_users)
               .exclude(user__in=banning_users)
               .exclude(ticket__user__in=banning_users)
               )

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
        'user_answered_tickets': user_answered_tickets,
        'user_review_tickets': user_review_tickets,
        'banning_users': banning_users
    }
    return render(request,
                  'reviews/flux.html',
                  context)


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
    banning_users = get_banning_users(request.user)

    # this two lists are used in context to display or not a button
    # list of user tickets that have had a review
    user_answered_tickets = Ticket.objects.filter(review__isnull=False,
                                                  user=request.user).distinct()
    # list of tickets that have a user review
    user_review_tickets = Ticket.objects.filter(
        review__user=request.user).distinct()

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
                  {'reviews_and_tickets': reviews_and_tickets,
                   'user_answered_tickets': user_answered_tickets,
                   'user_review_tickets': user_review_tickets,
                   'banning_users': banning_users})


@login_required
def follow(request):
    """
    Allows the user to follow another user.

    - On POST: Adds a new follow relationship if the form is valid.
    - On GET: Displays the follow form with a filtered user list.

    The user can only follow people he doesn’t already follow and who
    haven’t blocked him.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: Redirects on success, otherwise renders 'follow.html'.
    """

    banning_users = get_banning_users(request.user)

    banned_users = get_banned_users(request.user)

    followers_users = get_followers(request.user)

    following_users = get_followings(request.user)

    if request.method == "POST":
        form = FollowUserForm(request.POST, request.user)
        if form.is_valid():
            user_to_follow = form.cleaned_data['user']

            UserFollows.objects.create(user=request.user,
                                       followed_user=user_to_follow)
            messages.success(request,
                             f"Vous suivez maintenant {user_to_follow.username}.")
            return redirect('follow')

    else:
        form = FollowUserForm(current_user=request.user)

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
    # list of members who have banned the user.
    banning_users = get_banning_users(request.user)

    user_to_unfollow = get_object_or_404(User, id=user_id)

    # if the user to unsubscribe is not in the list
    if not banning_users.filter(id=user_to_unfollow.id).exists():
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

    if UserFollows.objects.filter(
            user=request.user,
            followed_user=user_to_ban
    ).exists():

        user_relation = get_object_or_404(
            UserFollows,
            user=request.user,
            followed_user=user_to_ban
        )
        user_relation.banned = True
    else:
        user_relation = UserFollows.objects.create(
            user=request.user,
            followed_user=user_to_ban,
            banned=True)

    user_relation.save()
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
    user_to_unban = get_object_or_404(User, id=user_id)
    follow_relation = get_object_or_404(UserFollows,
                                        user=request.user,
                                        followed_user=user_to_unban)
    follow_relation.delete()

    return redirect('follow')
