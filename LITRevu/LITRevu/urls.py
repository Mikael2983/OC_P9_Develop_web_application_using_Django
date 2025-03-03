"""
URL configuration for LITRevu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from authentification.views import reset_password, set_new_password, \
    password_reset_done,CustomLoginView, custom_logout, signup_page

from reviews import views as r_views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', CustomLoginView.as_view(
        template_name='authentification/login.html'),
         name='login'),
    path('logout/', custom_logout, name='logout'),

    path('signup/', signup_page, name='signup'),

    path('password-reset/', reset_password, name='reset_password'),
    path('password-reset/new/', set_new_password, name='set_new_password'),
    path('password-reset/done/', password_reset_done,
         name='password_reset_done'),

    path('', r_views.flux, name='flux'),
    path('follow/', r_views.follow, name='follow'),
    path('follow/<int:user_id>/unfollow', r_views.unfollow, name='unfollow'),
    path('follow/<int:user_id>/unsubscribe_followers', r_views.unsubscribe_followers, name='unsubscribe_followers'),
    path('follow/<int:user_id>/ban_followers', r_views.ban_followers, name='ban_followers'),
    path('follow/<int:user_id>/unban_followers', r_views.unban_followers, name='unban_followers'),

    path('posts/', r_views.user_posts, name='user_posts'),

    path('reviews/create-review/', r_views.create_review, name='create_review'),
    path('reviews/<int:review_id>/modify-review/', r_views.modify_review, name='modify_review'),

    path('tickets/create-ticket/', r_views.create_ticket, name='create_ticket'),
    path('tickets/<int:ticket_id>/modify-ticket/', r_views.modify_ticket, name='modify_ticket'),
    path('tickets/<int:ticket_id>/delete-ticket/', r_views.delete_ticket, name='delete_ticket'),
    path('tickets/<int:ticket_id>/answer-ticket/', r_views.answer_ticket, name='answer_ticket'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)