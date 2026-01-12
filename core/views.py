from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Car, Brand, Model
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CarForm


class CarListView(ListView):
    model = Car
    template_name = 'core/car_list.html'
    context_object_name = 'cars'
    queryset = Car.objects.filter(status='active').order_by('-created_at')
    paginate_by = 3


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
        return super().form_valid(form)


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
            return redirect('core:car_list')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('core:car_list')
