from django.contrib import admin

from natlas.accounts.models import User


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "is_active", "is_staff")
    search_fields = (
        "id",
        "email",
    )
    ordering = ("email",)
