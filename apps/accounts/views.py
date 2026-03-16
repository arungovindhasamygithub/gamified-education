from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def index_view(request):
    """Home page view"""
    return render(request, 'index.html')

def register_view(request):
    # PREVENT LOGGED-IN USERS FROM SEEING REGISTRATION
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('dashboard:admin_dashboard')
        elif request.user.role == 'teacher':
            return redirect('dashboard:teacher_dashboard')
        else:
            return redirect('dashboard:student_dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to EcoQuest.')
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect('dashboard:admin_dashboard')
            elif user.role == 'teacher':
                return redirect('dashboard:teacher_dashboard')
            else:
                return redirect('dashboard:student_dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    # PREVENT LOGGED-IN USERS FROM SEEING LOGIN PAGE
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('dashboard:admin_dashboard')
        elif request.user.role == 'teacher':
            return redirect('dashboard:teacher_dashboard')
        else:
            return redirect('dashboard:student_dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            # CORRECTION: form.get_user() is the proper way to get the user 
            # after an AuthenticationForm passes is_valid()
            user = form.get_user()
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                
                # ENHANCEMENT: Handle the 'next' parameter if they were redirected here
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                # Redirect based on role
                if user.role == 'admin':
                    return redirect('dashboard:admin_dashboard')
                elif user.role == 'teacher':
                    return redirect('dashboard:teacher_dashboard')
                else:
                    return redirect('dashboard:student_dashboard')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('index')