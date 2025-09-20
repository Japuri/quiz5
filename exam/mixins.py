# exam/mixins.py

from django.contrib.auth.mixins import AccessMixin

class StudentRequiredMixin(AccessMixin):
    """
    Mixin that verifies that the current user is a student.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.user_type == 'student':
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)