from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils import timezone
timezone.localtime(timezone.now())



from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class Exam(models.Model):
    ACCESS_TYPE_CHOICES = [
        ('all_students', 'All Students'),
        ('specific_students', 'Specific Students'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_exams',
        limit_choices_to={'user_type': 'teacher'}
    )
    start_date_time = models.DateTimeField()
    end_date_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    max_attempts = models.PositiveIntegerField(default=1)
    passing_percentage = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        default='specific_students'
    )
    allowed_students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='accessible_exams',
        blank=True,
        limit_choices_to={'user_type': 'student'}
    )
    total_marks = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'
    
    def __str__(self):
        return f"{self.title} - {self.teacher.get_full_name()}"
    
    def clean(self):
        if self.start_date_time and self.end_date_time:
            if self.start_date_time >= self.end_date_time:
                raise ValidationError('Start date must be before end date.')

    # ----------------- Status Methods -----------------
    def is_upcoming(self):
        return timezone.now() < self.start_date_time

    def is_expired(self):
        return timezone.now() > self.end_date_time

    def is_currently_active(self):
        now = timezone.now()
        return self.start_date_time <= now <= self.end_date_time

    @property
    def is_active_now(self):
        return self.is_currently_active()

    @property
    def is_upcoming_now(self):
        return self.is_upcoming()

    def can_student_access(self, student):
        if self.access_type == 'all_students' and student.user_type == 'student':
            return True
        return self.allowed_students.filter(id=student.id).exists()

    def get_total_students(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if self.access_type == 'all_students':
            return User.objects.filter(user_type='student').count()
        return self.allowed_students.count()

    def get_students_taken(self):
        return self.submissions.filter(is_completed=True).values('student').distinct().count()

    def get_student_attempts(self, student):
        return self.submissions.filter(student=student).count()

    def can_student_attempt(self, student):
        return self.get_student_attempts(student) < self.max_attempts

    def get_remaining_attempts(self, student):
        return max(0, self.max_attempts - self.get_student_attempts(student))

    def get_status_for_student(self, student):
        """Get exam status specifically for a student."""
        now = timezone.now()

        if now < self.start_date_time:
            return 'upcoming'
        elif now > self.end_date_time:
            return 'expired'

        if not self.can_student_access(student):
            return 'no_access'

        if not self.can_student_attempt(student):
            return 'no_attempts'

        ongoing = self.submissions.filter(student=student, is_completed=False).first()
        if ongoing:
            time_elapsed = now - ongoing.started_at
            if time_elapsed.total_seconds() > (self.duration_minutes * 60):
                return 'time_up'
            return 'in_progress'

        return 'available'

# --------------------------------------------------------------------------------------

class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['exam', 'order']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."

# --------------------------------------------------------------------------------------

class QuestionChoice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=500)
    choice_label = models.CharField(max_length=1, default='A')
    order = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['order']
        unique_together = ['question', 'order']
        verbose_name = 'Question Choice'
        verbose_name_plural = 'Question Choices'
    
    def __str__(self):
        return f"{self.choice_label}. {self.choice_text}"

# --------------------------------------------------------------------------------------

class AnswerKey(models.Model):
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='answer_key')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_answer_keys'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Answer Key'
        verbose_name_plural = 'Answer Keys'
    
    def __str__(self):
        return f"Answer Key for {self.exam.title}"

# --------------------------------------------------------------------------------------

class CorrectAnswer(models.Model):
    answer_key = models.ForeignKey(AnswerKey, on_delete=models.CASCADE, related_name='correct_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='correct_answer')
    correct_choice = models.ForeignKey(
        QuestionChoice, 
        on_delete=models.CASCADE,
        related_name='correct_answers'
    )
    explanation = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['answer_key', 'question']
        verbose_name = 'Correct Answer'
        verbose_name_plural = 'Correct Answers'
    
    def __str__(self):
        return f"Answer for Q{self.question.order}: {self.correct_choice.choice_label}"

# --------------------------------------------------------------------------------------

class ExamAccess(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='access_records')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_access_records',
        limit_choices_to={'user_type': 'student'}
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='granted_access_records'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['exam', 'student']
        verbose_name = 'Exam Access'
        verbose_name_plural = 'Exam Access Records'
    
    def __str__(self):
        status = "Revoked" if self.is_revoked else "Active"
        return f"{self.student.get_full_name()} - {self.exam.title} ({status})"

# --------------------------------------------------------------------------------------

class ExamSubmission(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_submissions',
        limit_choices_to={'user_type': 'student'}
    )
    attempt_number = models.PositiveIntegerField(default=1)
    score = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    time_taken = models.DurationField(null=True, blank=True)
    question_order = models.JSONField(default=list, help_text="Randomized order of question IDs for this attempt")
    auto_submitted = models.BooleanField(default=False, help_text="True if exam was auto-submitted due to time limit")
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Exam Submission'
        verbose_name_plural = 'Exam Submissions'
    
    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.student.get_full_name()} - {self.exam.title} (Attempt #{self.attempt_number}) ({status})"
    
    def calculate_percentage(self):
        if self.total_marks > 0:
            self.percentage = (self.score / self.total_marks) * 100
        else:
            self.percentage = 0.00
        return self.percentage
    
    def get_time_remaining(self):
        """Get remaining time in seconds for this submission."""
        if self.is_completed:
            return 0
        
        now = timezone.now()
        time_elapsed = (now - self.started_at).total_seconds()
        total_time = self.exam.duration_minutes * 60
        remaining = max(0, total_time - time_elapsed)
        return int(remaining)
    
    def is_time_up(self):
        """Check if time is up for this submission."""
        return self.get_time_remaining() <= 0
    
    def is_passed(self):
        """Check if the student passed this exam based on the passing percentage."""
        if not self.is_completed:
            return False
        return self.percentage >= self.exam.passing_percentage
    
    def get_result_status(self):
        """Get the result status (Pass/Fail) for this submission."""
        if not self.is_completed:
            return 'In Progress'
        return 'Pass' if self.is_passed() else 'Fail'
    
    def get_result_badge_class(self):
        """Get Bootstrap badge class for the result status."""
        if not self.is_completed:
            return 'badge-warning'
        return 'badge-success' if self.is_passed() else 'badge-danger'
    
    def save(self, *args, **kwargs):
        # Set attempt number if not set
        if not self.attempt_number:
            last_attempt = ExamSubmission.objects.filter(
                exam=self.exam, 
                student=self.student
            ).order_by('-attempt_number').first()
            self.attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1
        
        self.calculate_percentage()
        super().save(*args, **kwargs)

# --------------------------------------------------------------------------------------

class StudentAnswer(models.Model):
    submission = models.ForeignKey(ExamSubmission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(QuestionChoice, on_delete=models.CASCADE, null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['submission', 'question']
        verbose_name = 'Student Answer'
        verbose_name_plural = 'Student Answers'
    
    def __str__(self):
        choice_text = self.selected_choice.choice_label if self.selected_choice else "No answer"
        return f"{self.submission.student.get_full_name()} - Q{self.question.order}: {choice_text}"
    
    def is_correct(self):
        """Check if the selected answer is correct."""
        try:
            correct_answer = CorrectAnswer.objects.get(
                answer_key__exam=self.submission.exam,
                question=self.question
            )
            return self.selected_choice == correct_answer.correct_choice
        except CorrectAnswer.DoesNotExist:
            return False
