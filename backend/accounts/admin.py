from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import UserCreationForm
from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationForm
    # Le UserAdmin de Django cite username partout : chaque référence passe à email.
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "organization", "role", "is_staff")
    list_filter = ("role", "organization", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name")
    # Une seule requête pour afficher l'organisation de chaque ligne (pas de N+1).
    list_select_related = ("organization",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name")}),
        ("Organisation", {"fields": ("organization", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Dates importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "organization",
                    "role",
                    "usable_password",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
