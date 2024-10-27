from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    # Добавяне на действие за стартиране на нов сезон
    actions = ['start_new_season']

    def start_new_season(self, request, queryset):
        # Логиката за стартиране на нов сезон
        # Примерна логика за създаване на нов сезон
       pass

    start_new_season.short_description = "Стартирай нов сезон"


admin.site.register(CustomUser, CustomUserAdmin)
