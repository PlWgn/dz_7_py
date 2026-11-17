from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from .models import User


def get_employees():
    # суперпользователи - это администраторы сайта, а не сотрудники
    return User.objects.filter(is_superuser=False)


def get_employee_cards():
    return get_employees().prefetch_related('skills', 'photos')


class IndexView(ListView):
    template_name = 'employees/index.html'
    context_object_name = 'employees'

    def get_queryset(self):
        return get_employee_cards().order_by('-hire_date', '-id')[:4]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees_count'] = get_employees().count()
        return context


class EmployeeListView(ListView):
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10

    def get_queryset(self):
        return get_employee_cards()


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'

    def get_queryset(self):
        return (
            get_employees()
            .select_related('workplace')
            .prefetch_related('employee_skills__skill', 'photos')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photos = list(self.object.photos.all())
        context['main_photo'] = photos[0] if photos else None
        context['gallery'] = photos[1:]
        return context
