from django import forms
from .models import StudentProfileDetails, Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "description", "quota", "prerequisites"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. AI Chatbot for Student Support"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Briefly describe what the project is about..."}),
            "quota": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "prerequisites": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Python, Django, React"}),
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
            "department": forms.Select(attrs={"id": "id_department"}),
            "course": forms.Select(attrs={"id": "id_course"}),
            "academic_summary": forms.Textarea(attrs={"rows": 4}),
            "skills": forms.Textarea(attrs={"rows": 4}),
            "research_interests": forms.Textarea(attrs={"rows": 3}),
        }
