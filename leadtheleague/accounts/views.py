import os

from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth import login
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView
from accounts.forms import CustomUserCreationForm
from leadtheleague import settings
from teams.models import Team
from django.shortcuts import render

def welcome(request):
    avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
    avatars = [
        f"{settings.MEDIA_URL}avatars/{avatar}" for avatar in os.listdir(avatars_dir) if avatar.endswith(('.png', '.jpg', '.jpeg'))
    ]
    return render(request, 'accounts/welcome.html', {'avatars': avatars})


from django.http import JsonResponse

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('accounts')
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        user = form.save(commit=False)
        avatar_url = self.request.POST.get('avatar')
        if avatar_url:
            user.avatar = avatar_url.replace(settings.MEDIA_URL, '')

        user.save()
        login(self.request, user)

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "redirect_url": reverse_lazy('game:choose_team')})

        return redirect('game:choose_team')

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

        return self.render_to_response(self.get_context_data(form=form))

class CustomLoginView(LoginView):
    template_name = 'accounts/welcome.html'
    redirect_authenticated_user = False

def get_success_url(self):
    if not Team.objects.filter(user=self.request.user).exists():
        return reverse_lazy('teams:create_team')
    return reverse_lazy('game:home')

