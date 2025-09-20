from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, TemplateView
from django.views import View
from django.contrib import messages
from django.db.models import Count, Q, F, Avg, Sum
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.contrib.auth import get_user_model
from django import forms
from django.http import JsonResponse, HttpResponse
import random
import json
from django.contrib.auth import logout
from django.db.models import Case, When, IntegerField
from .mixins import StudentRequiredMixin
from django.db import models

from exam.forms import ExamForm
from .models import (
    Exam, Question, QuestionChoice, AnswerKey, CorrectAnswer, 
    ExamSubmission, StudentAnswer
)

User = get_user_model()


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, TemplateView
from django.views import View
from django.contrib import messages
from django.db.models import Count, Q, F, Avg, Sum
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.contrib.auth import get_user_model
from django import forms
from django.http import JsonResponse, HttpResponse
import random
import json
from django.contrib.auth import logout
from django.db.models import Case, When, IntegerField
from .mixins import StudentRequiredMixin
from django.db import models

from exam.forms import ExamForm
from .models import (
    Exam, Question, QuestionChoice, AnswerKey, CorrectAnswer, 
    ExamSubmission, StudentAnswer
)

User = get_user_model()


def debug_timezone_view(request):
    """
    Simple debug view for quick diagnostics (uses localtime).
    """
    now = timezone.localtime()
    tz = timezone.get_current_timezone_name()
    return HttpResponse(f"Now: {now.isoformat()} (timezone: {tz})")


class CustomLogoutView(View):
    """Logout and redirect to custom signin (avoid falling back to /admin/login/)."""
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse_lazy('authentication:signin'))
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse_lazy('authentication:signin'))


class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'exam/dashboard.html'
    context_object_name = 'exams'
    paginate_by = 12
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication:signin')
        
        if request.user.is_teacher:
            return TeacherDashboardView.as_view()(request, *args, **kwargs)
        elif request.user.is_student:
            return StudentDashboardView.as_view()(request, *args, **kwargs)
        else:
            messages.error(request, 'Access denied. Invalid user role.')
            return redirect('authentication:signin')


class TeacherDashboardView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exam/teacher_dashboard.html'
    context_object_name = 'exams'
    paginate_by = 12

    def get_queryset(self):
        # use localtime so displayed statuses match local times
        now = timezone.localtime()

        # Get all exams created by this teacher with priority ordering
        queryset = Exam.objects.filter(
            teacher=self.request.user
        ).annotate(
            priority=Case(
                # Active exams (currently running) - Priority 1
                When(
                    is_active=True,
                    start_date_time__lte=now,
                    end_date_time__gte=now,
                    then=1
                ),
                # Upcoming exams - Priority 2
                When(
                    is_active=True,
                    start_date_time__gt=now,
                    then=2
                ),
                # Expired exams - Priority 3
                When(
                    end_date_time__lt=now,
                    then=3
                ),
                # Disabled exams - Priority 4
                When(
                    is_active=False,
                    then=4
                ),
                default=4,
                output_field=IntegerField()
            )
        ).order_by('priority', 'start_date_time')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = 'Teacher'

        now = timezone.localtime()
        exams = Exam.objects.filter(teacher=self.request.user)

        context['total_exams'] = exams.count()
        context['active_exams'] = exams.filter(
            is_active=True,
            start_date_time__lte=now,
            end_date_time__gte=now
        ).count()
        context['upcoming_exams'] = exams.filter(
            is_active=True,
            start_date_time__gt=now
        ).count()
        context['expired_exams'] = exams.filter(
            end_date_time__lt=now
        ).count()
        context['disabled_exams'] = exams.filter(
            is_active=False
        ).count()

        return context

class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    model = Exam
    template_name = 'exam/student_dashboard.html'
    context_object_name = 'exams_with_status'
    paginate_by = 9
    
    def get_queryset(self):
        user = self.request.user
        assigned_exams = Exam.objects.filter(
            models.Q(access_type='all_students') | models.Q(allowed_students=user)
        ).distinct()
        return assigned_exams

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        exams_page = context['page_obj']
        
        exams_with_status = []
        for exam in exams_page.object_list:
            status = exam.get_status_for_student(user)
            attempts_made = exam.get_student_attempts(user)
            remaining_attempts = exam.get_remaining_attempts(user)

            exams_with_status.append({
                'exam': exam,
                'status': status,
                'attempts_made': attempts_made,
                'remaining_attempts': remaining_attempts,
            })

        context['exams_with_status'] = exams_with_status
        context['total_exams'] = self.get_queryset().count()
        context['available_exams'] = sum(1 for item in exams_with_status if item['status'] == 'available')
        context['upcoming_exams'] = sum(1 for item in exams_with_status if item['status'] == 'upcoming')
        
        return context


class ExamCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exam/create_exam.html'
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_teacher

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_students = User.objects.filter(user_type='student').count()
        context['total_students'] = total_students
        
        if total_students == 0:
            messages.warning(
                self.request, 
                'No students are registered in the system. You may need to register students before creating an exam.'
            )
        
        return context

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        messages.success(self.request, 'Exam created successfully! Now add questions to complete your exam.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('exam:exam_detail', kwargs={'pk': self.object.pk})

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Teachers only.')
        return redirect('exam:dashboard')


class QuestionManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_teacher

    def dispatch(self, request, *args, **kwargs):
        self.exam = get_object_or_404(Exam, pk=kwargs['exam_id'], teacher=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, exam_id):
        questions = self.exam.questions.all().order_by('order')
        context = {
            'exam': self.exam,
            'questions': questions,
            'total_questions': questions.count(),
        }
        return render(request, 'exam/manage_questions.html', context)

    def post(self, request, exam_id):
        action = request.POST.get('action')
        
        if (action == 'add_question'):
            return self._add_question(request)
        elif (action == 'delete_question'):
            return self._delete_question(request)
        elif (action == 'save_answers'):
            return self._save_answer_key(request)
        
        return redirect('exam:manage_questions', exam_id=exam_id)

    def _add_question(self, request):
        question_text = request.POST.get('question_text', '').strip()
        marks = request.POST.get('marks', 1)
        choices = [
            request.POST.get('choice_a', '').strip(),
            request.POST.get('choice_b', '').strip(),
            request.POST.get('choice_c', '').strip(),
            request.POST.get('choice_d', '').strip(),
        ]
        correct_answer = request.POST.get('correct_answer', '').upper()

        # Validation
        if not question_text:
            messages.error(request, 'Question text is required.')
            return redirect('exam:manage_questions', exam_id=self.exam.pk)

        if not all(choices):
            messages.error(request, 'All four choices (A, B, C, D) are required.')
            return redirect('exam:manage_questions', exam_id=self.exam.pk)

        if correct_answer not in ['A', 'B', 'C', 'D']:
            messages.error(request, 'Please select a valid correct answer (A, B, C, or D).')
            return redirect('exam:manage_questions', exam_id=self.exam.pk)

        try:
            with transaction.atomic():
                last_question = self.exam.questions.order_by('-order').first()
                next_order = (last_question.order + 1) if last_question else 1

                question = Question.objects.create(
                    exam=self.exam,
                    question_text=question_text,
                    marks=int(marks),
                    order=next_order
                )

                choice_labels = ['A', 'B', 'C', 'D']
                created_choices = []
                for i, choice_text in enumerate(choices):
                    choice = QuestionChoice.objects.create(
                        question=question,
                        choice_text=choice_text,
                        choice_label=choice_labels[i],
                        order=i + 1
                    )
                    created_choices.append(choice)

                answer_key, created = AnswerKey.objects.get_or_create(
                    exam=self.exam,
                    defaults={'created_by': request.user}
                )

                correct_choice = next(choice for choice in created_choices if choice.choice_label == correct_answer)
                CorrectAnswer.objects.create(
                    answer_key=answer_key,
                    question=question,
                    correct_choice=correct_choice
                )

                messages.success(request, f'Question {next_order} added successfully!')

        except Exception as e:
            messages.error(request, f'Error adding question: {str(e)}')

        return redirect('exam:manage_questions', exam_id=self.exam.pk)

    def _delete_question(self, request):
        question_id = request.POST.get('question_id')
        try:
            question = Question.objects.get(id=question_id, exam=self.exam)
            question_order = question.order
            question.delete()
            
            remaining_questions = self.exam.questions.filter(order__gt=question_order).order_by('order')
            for i, q in enumerate(remaining_questions):
                q.order = question_order + i
                q.save()

            messages.success(request, 'Question deleted successfully!')
        except Question.DoesNotExist:
            messages.error(request, 'Question not found.')
        except Exception as e:
            messages.error(request, f'Error deleting question: {str(e)}')

        return redirect('exam:manage_questions', exam_id=self.exam.pk)

    def _save_answer_key(self, request):
        try:
            changes_made = False
            with transaction.atomic():
                answer_key, created = AnswerKey.objects.get_or_create(
                    exam=self.exam,
                    defaults={'created_by': request.user}
                )

                for question in self.exam.questions.all():
                    correct_choice_id = request.POST.get(f'question_{question.id}_answer')
                    
                    if correct_choice_id:
                        try:
                            correct_choice = QuestionChoice.objects.get(
                                id=correct_choice_id, 
                                question=question
                            )
                            
                            existing_answer = CorrectAnswer.objects.filter(
                                answer_key=answer_key,
                                question=question
                            ).first()
                            
                            if not existing_answer or existing_answer.correct_choice_id != int(correct_choice_id):
                                changes_made = True
                            
                            CorrectAnswer.objects.update_or_create(
                                answer_key=answer_key,
                                question=question,
                                defaults={'correct_choice': correct_choice}
                            )
                        except QuestionChoice.DoesNotExist:
                            continue

                if changes_made:
                    messages.success(request, 'Answer key updated successfully!')
                else:
                    messages.info(request, 'No changes were made to the answer key.')
                    
        except Exception as e:
            messages.error(request, f'Error saving answer key: {str(e)}')

        return redirect('exam:manage_questions', exam_id=self.exam.pk)


class ExamDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Exam
    template_name = 'exam/exam_detail.html'
    context_object_name = 'exam'

    def test_func(self):
        exam = self.get_object()
        return self.request.user.is_teacher and exam.teacher == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. You can only view exams you created.')
        return redirect('exam:teacher_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = self.object
        
        if exam.access_type == 'all_students':
            eligible_students = User.objects.filter(user_type='student')
        else:
            eligible_students = exam.allowed_students.all()
        
        student_data = []
        for student in eligible_students:
            try:
                submission = ExamSubmission.objects.get(exam=exam, student=student)
                if submission.is_completed:
                    status = 'Completed'
                    score_display = f"{submission.score}/{submission.total_marks} ({submission.percentage:.1f}%)"
                    submitted_at = submission.submitted_at
                else:
                    status = 'In Progress'
                    score_display = 'In Progress'
                    submitted_at = None
            except ExamSubmission.DoesNotExist:
                status = 'Not Started'
                score_display = 'Did not take yet'
                submitted_at = None
            
            student_data.append({
                'student': student,
                'status': status,
                'score_display': score_display,
                'submitted_at': submitted_at,
            })
        
        student_data.sort(key=lambda x: (x['status'] != 'Completed', x['student'].get_full_name()))
        
        total_students = len(student_data)
        completed_submissions = len([s for s in student_data if s['status'] == 'Completed'])
        in_progress = len([s for s in student_data if s['status'] == 'In Progress'])
        not_started = len([s for s in student_data if s['status'] == 'Not Started'])
        
        completed_submissions_objects = ExamSubmission.objects.filter(
            exam=exam, 
            is_completed=True
        )
        from django.db import models
        average_score = completed_submissions_objects.aggregate(
            avg_score=models.Avg('percentage')
        )['avg_score'] or 0
        
        context.update({
            'student_data': student_data,
            'total_students': total_students,
            'completed_count': completed_submissions,
            'in_progress_count': in_progress,
            'not_started_count': not_started,
            'average_score': round(average_score, 1),
            'total_questions': exam.questions.count(),
            'can_edit': not exam.is_expired(),
        })
        
        return context


class ExamUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exam/edit_exam.html'
    
    def test_func(self):
        exam = self.get_object()
        return (self.request.user.is_teacher and 
                exam.teacher == self.request.user and 
                not exam.is_expired())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_students = User.objects.filter(user_type='student').count()
        context['total_students'] = total_students
        
        if total_students == 0:
            messages.warning(
                self.request, 
                'No students are registered in the system. You may need to register students before updating this exam.'
            )
        
        return context
    
    def handle_no_permission(self):
        exam = self.get_object()
        if exam.is_expired():
            messages.error(self.request, 'Cannot edit exam after the deadline has passed.')
        else:
            messages.error(self.request, 'Access denied. You can only edit exams you created.')
        return redirect('exam:exam_detail', pk=exam.pk)
    
    def form_valid(self, form):
        messages.success(self.request, 'Exam updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('exam:exam_detail', kwargs={'pk': self.object.pk})


class StudentExamView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Exam
    template_name = 'exam/student_exam.html'
    context_object_name = 'exam'
    
    def test_func(self):
        return self.request.user.is_student

    def dispatch(self, request, *args, **kwargs):
        """
        Enforce access restrictions on the detailed exam page.
        This prevents direct URL bypass of the dashboard logic.
        """
        exam = self.get_object()
        user = self.request.user
        
        status = exam.get_status_for_student(user)

        if status == 'upcoming':
            messages.warning(request, 'This exam is not yet available. Please check back later.')
            return redirect('exam:student_dashboard')
        elif status == 'expired':
            messages.error(request, 'This exam has expired.')
            return redirect('exam:student_dashboard')
        elif status == 'no_attempts':
            messages.error(request, 'You have no remaining attempts for this exam.')
            return redirect('exam:student_dashboard')
        elif status == 'no_access':
            messages.error(request, 'You do not have permission to access this exam.')
            return redirect('exam:student_dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = self.get_object()
        student = self.request.user
        
        context['attempts_made'] = exam.get_student_attempts(student)
        context['remaining_attempts'] = exam.get_remaining_attempts(student)
        context['max_attempts'] = exam.max_attempts
        
        ongoing_submission = exam.submissions.filter(
            student=student, 
            is_completed=False
        ).first()
        
        if ongoing_submission and not ongoing_submission.is_time_up():
            context['ongoing_submission'] = ongoing_submission
            context['time_remaining'] = ongoing_submission.get_time_remaining()
        
        completed_submissions = exam.submissions.filter(
            student=student,
            is_completed=True
        ).order_by('-submitted_at')
        context['completed_submissions'] = completed_submissions
        
        return context
    
    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Students only.')
        return redirect('exam:dashboard')


class StartExamView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View to start or resume a new exam attempt."""
    
    def test_func(self):
        return self.request.user.is_student
    
    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        student = request.user
        
        status = exam.get_status_for_student(student)
        
        # Case 1: Exam is unavailable for any reason
        if status not in ['available', 'in_progress']:
            if status == 'upcoming':
                messages.warning(request, 'This exam is not yet available. Please check back later.')
            elif status == 'expired':
                messages.error(request, 'This exam has expired.')
            elif status == 'no_attempts':
                messages.error(request, 'You have no remaining attempts for this exam.')
            elif status == 'no_access':
                messages.error(request, 'You do not have permission to access this exam.')
            
            return redirect('exam:student_dashboard')

        # Case 2: Exam is available to start a new attempt
        if status == 'available':
            try:
                with transaction.atomic():
                    questions = list(exam.questions.values_list('id', flat=True))
                    random.shuffle(questions)
                    
                    submission = ExamSubmission.objects.create(
                        exam=exam,
                        student=student,
                        total_marks=exam.total_marks,
                        question_order=questions
                    )
                    
                    messages.success(request, f'Exam started! You have {exam.duration_minutes} minutes to complete.')
                    return redirect('exam:take_exam', submission_id=submission.id)
            except Exception as e:
                messages.error(request, f'Failed to start exam. Error: {e}')
                return redirect('exam:student_dashboard')

        # Case 3: Exam is in progress, so we need to resume the existing attempt
        elif status == 'in_progress':
            submission = ExamSubmission.objects.filter(
                exam=exam,
                student=student,
                is_completed=False
            ).first()
            
            if submission:
                messages.info(request, 'You have an ongoing attempt. Resuming exam.')
                return redirect('exam:take_exam', submission_id=submission.id)
            else:
                # Fallback in case of a data discrepancy
                messages.error(request, 'Could not find ongoing submission.')
                return redirect('exam:student_dashboard')
    
    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Students only.')
        return redirect('exam:dashboard')

class TakeExamView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View for student to take the exam"""
    
    def test_func(self):
        return self.request.user.is_student
    
    def get_submission(self, submission_id):
        """Get submission and verify it belongs to current user"""
        return get_object_or_404(
            ExamSubmission,
            id=submission_id,
            student=self.request.user,
            is_completed=False
        )
    
    def get(self, request, submission_id):
        submission = self.get_submission(submission_id)
        
        if submission.is_time_up():
            return self.auto_submit_exam(submission)
        
        question_ids = submission.question_order
        questions = []
        
        for q_id in question_ids:
            try:
                question = Question.objects.get(id=q_id, exam=submission.exam)
                questions.append(question)
            except Question.DoesNotExist:
                continue
        
        existing_answers = {}
        for answer in submission.answers.all():
            existing_answers[answer.question.id] = answer.selected_choice.id if answer.selected_choice else None
        
        context = {
            'submission': submission,
            'exam': submission.exam,
            'questions': questions,
            'existing_answers': existing_answers,
            'time_remaining': submission.get_time_remaining(),
            'total_questions': len(questions),
        }
        
        return render(request, 'exam/take_exam.html', context)
    
    def post(self, request, submission_id):
        submission = self.get_submission(submission_id)
        
        if submission.is_time_up():
            return self.auto_submit_exam(submission)
        
        action = request.POST.get('action')
        
        if action == 'save_answer':
            return self.save_answer(request, submission)
        elif action == 'submit_exam':
            return self.submit_exam(request, submission)
        elif action == 'get_time':
            return JsonResponse({'time_remaining': submission.get_time_remaining()})
        
        return redirect('exam:take_exam', submission_id=submission_id)
    
    def save_answer(self, request, submission):
        """Save student's answer to a question"""
        question_id = request.POST.get('question_id')
        choice_id = request.POST.get('choice_id')
        
        try:
            question = Question.objects.get(id=question_id, exam=submission.exam)
            choice = QuestionChoice.objects.get(id=choice_id, question=question) if choice_id else None
            
            answer, created = StudentAnswer.objects.update_or_create(
                submission=submission,
                question=question,
                defaults={'selected_choice': choice}
            )
            
            return JsonResponse({'success': True, 'message': 'Answer saved'})
            
        except (Question.DoesNotExist, QuestionChoice.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Invalid question or choice'})
    
    def submit_exam(self, request, submission):
        """Submit the exam"""
        try:
            with transaction.atomic():
                submission.submitted_at = timezone.now()
                submission.is_completed = True
                submission.time_taken = submission.submitted_at - submission.started_at
                
                score = 0
                total_marks = submission.exam.questions.aggregate(
                    total=Sum('marks')
                )['total'] or 0
                
                for answer in submission.answers.all():
                    if answer.is_correct():
                        score += answer.question.marks
                
                submission.score = score
                submission.total_marks = total_marks
                submission.calculate_percentage()
                submission.save()
                
                messages.success(request, f'Exam submitted successfully! Your score: {score}/{submission.total_marks}')
                return redirect('exam:exam_result', submission_id=submission.id)
                
        except Exception as e:
            messages.error(request, 'Failed to submit exam. Please try again.')
            return redirect('exam:take_exam', submission_id=submission.id)
    
    def auto_submit_exam(self, submission):
        """Auto-submit exam when time is up"""
        if not submission.is_completed:
            try:
                with transaction.atomic():
                    submission.submitted_at = timezone.now()
                    submission.is_completed = True
                    submission.auto_submitted = True
                    submission.time_taken = timezone.timedelta(minutes=submission.exam.duration_minutes)
                    
                    score = 0
                    total_marks = submission.exam.questions.aggregate(
                        total=Sum('marks')
                    )['total'] or 0
                    
                    for answer in submission.answers.all():
                        if answer.is_correct():
                            score += answer.question.marks
                    
                    submission.score = score
                    submission.total_marks = total_marks
                    submission.calculate_percentage()
                    submission.save()
                    
                    messages.warning(self.request, 'Time is up! Your exam has been automatically submitted.')
            except:
                pass
        
        return redirect('exam:exam_result', submission_id=submission.id)
    
    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Students only.')
        return redirect('exam:dashboard')


class ExamResultView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View to show exam results"""
    model = ExamSubmission
    template_name = 'exam/exam_result.html'
    context_object_name = 'submission'
    pk_url_kwarg = 'submission_id'
    
    def test_func(self):
        submission = self.get_object()
        return (self.request.user.is_student and 
                submission.student == self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = self.get_object()
        
        answers_data = []
        for answer in submission.answers.all():
            try:
                correct_answer = CorrectAnswer.objects.get(
                    answer_key__exam=submission.exam,
                    question=answer.question
                )
                is_correct = answer.selected_choice == correct_answer.correct_choice
                points_earned = answer.question.marks if is_correct else 0
            except CorrectAnswer.DoesNotExist:
                is_correct = False
                points_earned = 0
                correct_answer = None
            
            answers_data.append({
                'question': answer.question,
                'selected_choice': answer.selected_choice,
                'correct_choice': correct_answer.correct_choice if correct_answer else None,
                'is_correct': is_correct,
                'points_earned': points_earned,
                'explanation': correct_answer.explanation if correct_answer else '',
            })
        
        context['answers_data'] = answers_data
        context['percentage'] = submission.percentage
        
        return context
    
    def handle_no_permission(self):
        messages.error(self.request, 'Access denied.')
        return redirect('exam:dashboard')


class StudentProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'authentication/student_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user
        context['student'] = student

        accessible_exams = Exam.objects.filter(
            Q(access_type='all_students') |
            Q(allowed_students=student),
            is_active=True
        ).distinct()

        exam_performance = []
        total_score = 0
        total_exams_taken = 0

        for exam in accessible_exams:
            submission = ExamSubmission.objects.filter(exam=exam, student=student).first()

            if submission:
                total_exams_taken += 1
                total_score += submission.percentage

                if submission.percentage >= exam.passing_percentage:
                    result_status = 'Passed'
                    badge_class = 'bg-success'
                else:
                    result_status = 'Failed'
                    badge_class = 'bg-danger'
            else:
                result_status = 'Not Taken'
                badge_class = 'bg-secondary'

            exam_performance.append({
                'exam': exam,
                'submission': submission,
                'result_status': result_status,
                'badge_class': badge_class,
            })

        avg_score = round(total_score / total_exams_taken, 2) if total_exams_taken else 0

        grade_ranges = {
            'A (90-100%)': 0,
            'B (80-89%)': 0,
            'C (70-79%)': 0,
            'D (60-69%)': 0,
            'F (<60%)': 0
        }
        for perf in exam_performance:
            sub = perf['submission']
            if sub:
                perc = sub.percentage
                if perc >= 90:
                    grade_ranges['A (90-100%)'] += 1
                elif perc >= 80:
                    grade_ranges['B (80-89%)'] += 1
                elif perc >= 70:
                    grade_ranges['C (70-79%)'] += 1
                elif perc >= 60:
                    grade_ranges['D (60-69%)'] += 1
                else:
                    grade_ranges['F (<60%)'] += 1

        context.update({
            'exam_performance': exam_performance,
            'avg_score': avg_score,
            'total_exams_taken': total_exams_taken,
            'grade_ranges': grade_ranges.items()
        })

        return context