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

    # list of user reviews and those he follows
    reviews = Review.objects.filter(
        Q(user__in=list_users) |
        Q(ticket__in=Ticket.objects.filter(user__in=list_users))
    ).exclude(ticket__user__in=banned_users)

    # list of user’s tickets and those he follows
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
def create_ticket(request):
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
    ticket = Ticket.objects.get(id=ticket_id)

    if request.user != ticket.user:
        return redirect(reverse('flux'))

    if request.method == 'POST':
        ticket.delete()
        return redirect(reverse('user_tickets'))

    return render(request,
                  'reviews/delete_ticket.html',
                  {'ticket': ticket})


@login_required
def follow(request):
    banned_users = User.objects.filter(following__followed_user=request.user,
                                        following__banned=True)

    banning_users = User.objects.filter(followers__user=request.user,
                                       followers__banned=True)
    print(f'banned_users: {banned_users}')
    print(f'banning_users: {banning_users}')
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

                if UserFollows.objects.filter(user=user_to_follow,
                                              followed_user=request.user).exists():
                    user_relation = get_object_or_404(UserFollows,
                                                      user=user_to_follow,
                                                      followed_user=request.user)
                    if user_relation.banned:
                        messages.error(request,
                                       "cet utilisateur vous a bloqué")
                        return redirect('follow')
                if user_to_follow == request.user:
                    messages.error(request,
                                   "Vous ne pouvez pas vous suivre vous-même.")
                elif UserFollows.objects.filter(user=request.user,
                                                followed_user=user_to_follow).exists():
                    messages.error(request,
                                   "Vous suivez déjà cet utilisateur.")
                else:
                    UserFollows.objects.create(user=request.user,
                                               followed_user=user_to_follow)
                    return redirect(
                        'follow')  # Redirection pour éviter le repost du formulaire

    else:
        form = FollowUserForm()

    return render(request, 'reviews/follow.html', {
        'form': form,
        'followers_users': followers_users,
        'following_users': following_users,
        'banned_users': banned_users,
        'banning_users': banning_users,

    })


@login_required
def unfollow(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)
    follow_relation = UserFollows.objects.filter(user=request.user,
                                                 followed_user=user_to_unfollow)
    follow_relation.delete()
    return redirect('follow')


@login_required
def unsubscribe_followers(request, user_id):
    print(user_id)
    user_to_unsubscribe = get_object_or_404(User, id=user_id)
    print(user_to_unsubscribe)
    follow_relation = UserFollows.objects.filter(user=user_to_unsubscribe,
                                                 followed_user=request.user)
    print(follow_relation)
    follow_relation.delete()

    return redirect('follow')


@login_required
def ban_followers(request, user_id):
    user_to_ban = get_object_or_404(User, id=user_id)
    follow_relation = get_object_or_404(UserFollows,
                                        user=user_to_ban,
                                        followed_user=request.user)
    follow_relation.banned = True
    follow_relation.save()
    return redirect('follow')


@login_required
def unban_followers(request, user_id):
    user_to_ban = get_object_or_404(User, id=user_id)
    follow_relation = get_object_or_404(UserFollows,
                                        user=user_to_ban,
                                        followed_user=request.user)
    follow_relation.banned = False
    follow_relation.save()
    return redirect('follow')
