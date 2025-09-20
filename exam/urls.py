from django.urls import path
from . import views
from .views import (
    DashboardView, 
    TeacherDashboardView, 
    StudentDashboardView, 
    ExamCreateView, 
    QuestionManagementView,
    ExamDetailView,
    ExamUpdateView,
    StudentExamView,
    StartExamView,
    TakeExamView,
    ExamResultView,
    debug_timezone_view,
    CustomLogoutView,
    StudentProfileView,
)

app_name = 'exam'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('teacher-dashboard/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('student-dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('student/profile/', views.StudentProfileView.as_view(), name='student_profile'),

    path('create/', views.ExamCreateView.as_view(), name='create_exam'),
    path('<int:pk>/', views.ExamDetailView.as_view(), name='exam_detail'),
    path('<int:pk>/edit/', views.ExamUpdateView.as_view(), name='edit_exam'),
    path('<int:exam_id>/questions/', views.QuestionManagementView.as_view(), name='manage_questions'),

    # Student exam taking URLs
    path('<int:pk>/student/', views.StudentExamView.as_view(), name='student_exam'),
    path('<int:pk>/start/', views.StartExamView.as_view(), name='start_exam'),
    path('take/<int:submission_id>/', views.TakeExamView.as_view(), name='take_exam'),
    path('result/<int:submission_id>/', views.ExamResultView.as_view(), name='exam_result'),

    path('debug-timezone/', views.debug_timezone_view, name='debug_timezone'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('exam/<int:pk>/start/', views.StartExamView.as_view(), name='start_exam'),
]
