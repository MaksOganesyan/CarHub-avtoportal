from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .models import Car, Brand, Model
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CarForm


class CarListView(ListView):
    model = Car
    template_name = 'core/car_list.html'
    context_object_name = 'cars'
    queryset = Car.objects.filter(status='active').order_by('-created_at')
    paginate_by = 10


class CarDetailView(DetailView):
    model = Car
    template_name = 'core/car_detail.html'
    context_object_name = 'car'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photos'] = self.object.photos.all()
        return context


class CarCreateView(LoginRequiredMixin, CreateView):
    model = Car
    form_class = CarForm          # ← только это
    template_name = 'core/car_form.html'
    success_url = reverse_lazy('core:car_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.all()
        context['models'] = Model.objects.all()
        return context

    def form_valid(self, form):   # ← только form, без request
        form.instance.user = self.request.user
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    model = Car
    form_class = CarForm
    template_name = 'core/car_form.html'
    success_url = reverse_lazy('core:car_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.all()
        context['models'] = Model.objects.all()
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Объявление успешно добавлено!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Проверьте данные. Есть ошибки в форме.')
        return super().form_invalid(form)


class CarUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Car
    form_class = CarForm
    template_name = 'core/car_form.html'
    success_url = reverse_lazy('core:car_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.all()
        context['models'] = Model.objects.all()
        return context

    def test_func(self):
        car = self.get_object()
        return self.request.user == car.user


class CarDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Car
    template_name = 'core/car_confirm_delete.html'
    success_url = reverse_lazy('core:car_list')

    def test_func(self):
        car = self.get_object()
        return self.request.user == car.user


# Регистрация и логин
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('core:car_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('core:car_list')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('core:car_list')
