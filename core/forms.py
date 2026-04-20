from django import forms
from .models import StudentProfileDetails, Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "description", "quota", "prerequisites"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. AI Chatbot for Student Support"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Briefly describe what the project is about..."}),
            "quota": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 50}),
            "prerequisites": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Python, Django, React"}),
        }
        error_messages = {
            "quota": {
                "min_value": "Project quota must be at least 1.",
                "max_value": "Project quota cannot exceed 50 students.",
                "invalid": "Please enter a valid whole number.",
            }
        }


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfileDetails
        fields = [
            "student_number",
            "department",
            "course",
            "academic_summary",
            "skills",
            "research_interests",
        ]
        widgets = {
            "student_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 210123456"}),
            "department": forms.Select(attrs={"class": "form-control", "id": "id_department"}),
            "course": forms.Select(attrs={"class": "form-control", "id": "id_course"}),
            "academic_summary": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "skills": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "research_interests": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        error_messages = {
            "student_number": {
                "invalid": "Student ID must contain only numbers.",
                "max_length": "Student ID is too long.",
            }
        }

class AllocationForm(forms.Form):
    weight_preference = forms.IntegerField(label="Preference Weight (0-100)",initial=70)
    weight_academic = forms.IntegerField(label="Qualification Weight (0-100)",initial=30)
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data