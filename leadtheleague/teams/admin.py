from django.contrib import admin, messages
from players.utils.generate_player_utils import generate_team_players
from .models import Team, TeamFinance

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'user',)
    search_fields = ('name', 'abbreviation', 'user__username')

    def fill_selected_teams_with_players(self, request, queryset):
        successful_teams = 0
        for team in queryset:
            try:
                generate_team_players(team)
                successful_teams += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Error generating players for team {team.name}: {e}",
                    level=messages.ERROR
                )
        self.message_user(
            request,
            f"Players successfully generated for {successful_teams} team(s).",
            level=messages.SUCCESS
        )

    actions = ['fill_selected_teams_with_players']
    fill_selected_teams_with_players.short_description = "Fill Selected Teams with Players"


# Финансовият админ за отбори
@admin.register(TeamFinance)
class TeamFinanceAdmin(admin.ModelAdmin):
    list_display = ('team', 'balance', 'total_income', 'total_expenses')  # Основни полета
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
