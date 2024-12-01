from django.contrib import admin, messages
from .models import Team, DummyTeamNames, TeamFinance
from .utils.generate_team_utils import fill_dummy_teams

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'user', 'division', 'is_dummy')
    search_fields = ('name', 'abbreviation', 'user__username')
    actions = ['fill_with_dummy_teams']  # Register the action to fill divisions with dummy teams

    def fill_with_dummy_teams(self, request, queryset):
        fill_dummy_teams()  # Call the utility function to create dummy teams
        self.message_user(request, "Dummy teams created and divisions filled.", level=messages.SUCCESS)

    fill_with_dummy_teams.short_description = "Create Dummy Teams to Fill Divisions"  # Set a descriptive label

@admin.register(DummyTeamNames)
class AdjectiveTeamNamesAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')  # Adjust this if your model has other fields
    search_fields = ('name', 'abbreviation')  # Enable searching by the adjective word

# Финансовият админ за отбори
@admin.register(TeamFinance)
class TeamFinanceAdmin(admin.ModelAdmin):
    list_display = ('team', 'balance', 'total_income', 'total_expenses')  # Основни полета
    list_filter = ('team__division',)  # Филтриране по дивизия на отбора
    search_fields = ('team__name',)  # Търсене по име на отбор
    readonly_fields = ('total_income', 'total_expenses')  # Полетата за приходи и разходи са само за четене

    def add_income(self, request, queryset):
        for finance in queryset:
            finance.balance += 1000  # Примерно добавяне на фиксирана сума
            finance.total_income += 1000
            finance.save()
        self.message_user(request, "Income added to selected teams.", level=messages.SUCCESS)

    def deduct_expense(self, request, queryset):
        for finance in queryset:
            if finance.balance >= 500:  # Проверка за достатъчен баланс
                finance.balance -= 500  # Примерно изваждане на фиксирана сума
                finance.total_expenses += 500
                finance.save()
            else:
                self.message_user(
                    request,
                    f"Not enough balance for {finance.team.name} to deduct expense.",
                    level=messages.WARNING
                )
        self.message_user(request, "Expenses deducted from selected teams.", level=messages.SUCCESS)

    actions = ['add_income', 'deduct_expense']  # Добавяне на действия
    add_income.short_description = "Add Income to Selected Teams"
    deduct_expense.short_description = "Deduct Expense from Selected Teams"
