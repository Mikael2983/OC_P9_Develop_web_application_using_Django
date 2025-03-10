from django.contrib import admin
from django.contrib.admin import ModelAdmin

from reviews.models import UserFollows, Review, Ticket


class TicketAdmin(ModelAdmin):
    list_display = ["id",
                    "title",
                    "user",
                    "answered",
                    "picture",
                    "time_created"
                    ]


class ReviewAdmin(ModelAdmin):
    list_display = ["id",
                    "headline",
                    "user",
                    "ticket"
                    ]


class UserAdmin(ModelAdmin):
    list_display = ["user",
                    "followed_user",
                    "banned"
                    ]


admin.site.register(Ticket, TicketAdmin)

admin.site.register(Review, ReviewAdmin)

admin.site.register(UserFollows, UserAdmin)
