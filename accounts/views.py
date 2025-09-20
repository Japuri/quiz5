from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model, logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.contrib import messages
from django.conf import settings
from exam.models import ExamSubmission
# Import exam models
from exam.models import ExamResult

User = get_user_model()


class CustomLogoutView(LogoutView):
    """
    Redirect to our custom signin page after logout.
    """
    next_page = reverse_lazy("auth-signin")

    def get_next_page(self):
        return reverse_lazy("auth-signin")


def logout_view(request):
    """
    Simple function-based logout fallback.
    """
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL or "/auth/signin/")


class StudentProfileView(LoginRequiredMixin, DetailView):
    """
    Shows student profile and exam statistics:
      - total_exams (attempts made)
      - passed_exams
      - failed_exams
      - pass_rate (percentage)
    """
    model = User
    template_name = "accounts/student_profile.html"
    context_object_name = "student"

    def get_object(self, queryset=None):
        # Student views their own profile
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user

        # Use ExamResult to calculate stats
        results = ExamResult.objects.filter(student=student)

        total_exams = results.count()
        passed = results.filter(percentage__gte=50).count()
        failed = total_exams - passed
        pass_rate = (passed / total_exams) * 100 if total_exams > 0 else 0

        context.update({
            "total_exams": total_exams,
            "total_exams_taken": total_exams,
            "passed_exams": passed,
            "failed_exams": failed,
            "pass_rate": round(pass_rate, 2),
        })
        return context

