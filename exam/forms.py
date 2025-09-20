from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

from django.utils import timezone

from .models import Exam

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title', 'description', 'start_date_time', 'end_date_time', 
            'duration_minutes', 'max_attempts', 'passing_percentage', 'access_type', 'allowed_students'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': True}),
            'end_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': True}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'required': True}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'required': True}),
            'passing_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100, 'required': True}),
            'access_type': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'allowed_students': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show students in the allowed_students field
        self.fields['allowed_students'].queryset = User.objects.filter(user_type='student')
        self.fields['allowed_students'].help_text = 'Hold Ctrl/Cmd to select multiple students'
        
        # Convert datetime fields to local timezone for display
        if self.instance and self.instance.pk:
            if self.instance.start_date_time:
                local_start = timezone.localtime(self.instance.start_date_time)
                self.fields['start_date_time'].initial = local_start.strftime('%Y-%m-%dT%H:%M')
            if self.instance.end_date_time:
                local_end = timezone.localtime(self.instance.end_date_time)
                self.fields['end_date_time'].initial = local_end.strftime('%Y-%m-%dT%H:%M')
    
    def clean(self):
        cleaned_data = super().clean()
        access_type = cleaned_data.get('access_type')
        allowed_students = cleaned_data.get('allowed_students')
        start_date_time = cleaned_data.get('start_date_time')
        end_date_time = cleaned_data.get('end_date_time')
        
        # Validate that there are students available when access_type is 'all_students'
        if access_type == 'all_students':
            total_students = User.objects.filter(user_type='student').count()
            if total_students == 0:
                raise forms.ValidationError(
                    'Cannot create exam for "All Students" because there are no students registered in the system. '
                    'Please register students first or change access type to "Specific Students".'
                )
        
        # Final validation: ensure exam has participants
        if access_type == 'specific_students':
            if not allowed_students or len(allowed_students) == 0:
                raise forms.ValidationError(
                    'This exam has no participants. Please select at least one student or change access type to "All Students".'
                )
        elif access_type == 'all_students':
            total_students = User.objects.filter(user_type='student').count()
            if total_students == 0:
                raise forms.ValidationError(
                    'Cannot create exam because there are no students in the system. Please register students first.'
                )
        
        # Validate that start time is before end time
        if start_date_time and end_date_time and start_date_time >= end_date_time:
            raise forms.ValidationError(
                'Start date and time must be before end date and time.'
            )
        
        return cleaned_data