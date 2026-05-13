from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages


def register_view(request):
    """Inscription d'un nouvel utilisateur."""
    if request.user.is_authenticated:
        return redirect('converter-home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenue {user.username} ! Ton compte a été créé.')
            return redirect('converter-home')
    else:
        form = UserCreationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Connexion d'un utilisateur existant."""
    if request.user.is_authenticated:
        return redirect('converter-home')

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bon retour {user.username} !')
            return redirect('converter-home')
        else:
            messages.error(request, 'Identifiants incorrects.')
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """Déconnexion."""
    logout(request)
    messages.info(request, 'Tu as été déconnecté.')
    return redirect('login')