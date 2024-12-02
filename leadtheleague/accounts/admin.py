from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    actions = ['send_test_email']  # Регистрация на действието за имейли

    def send_test_email(self, request, queryset):
        """
        Изпраща тестов имейл до избраните потребители.
        """
        # Проверка дали са избрани потребители
        if not queryset:
            self.message_user(request, "Не са избрани потребители за изпращане на имейл.", messages.WARNING)
            return

        successful_emails = 0
        for user in queryset:
            if user.email:  # Проверява дали потребителят има имейл
                try:
                    send_mail(
                        subject='leadtheleague',
                        message=f'Здравей, {user.username}! Това е тестов имейл от системата.',
                        from_email='ponetr@abv.bg',
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    successful_emails += 1
                except Exception as e:
                    self.message_user(request, f"Грешка при изпращане до {user.email}: {str(e)}", messages.ERROR)

        # Съобщение за успех
        self.message_user(
            request,
            f"Тестовите имейли бяха изпратени успешно до {successful_emails} потребител(и).",
            messages.SUCCESS
        )

    send_test_email.short_description = "Изпрати тестов имейл"


admin.site.register(CustomUser, CustomUserAdmin)
