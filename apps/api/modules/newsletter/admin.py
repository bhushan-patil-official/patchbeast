from django.contrib import admin

from .models import DigestRun, Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "confirmed", "games", "confirmed_at", "unsubscribed_at", "created_at")
    list_filter = ("confirmed",)
    search_fields = ("email",)
    readonly_fields = ("confirm_token", "unsub_token")


@admin.register(DigestRun)
class DigestRunAdmin(admin.ModelAdmin):
    list_display = ("iso_week", "item_count", "recipients", "sent", "created_at")
