# app_name/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, Supervisor, Admin, Project


def home(request):
    """
    Home = Login page.
    Uses real backend validation against Student / Supervisor / Admin tables.
    """
    error = None

    if request.method == "POST":
        role = request.POST.get("role")
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        # Basic empty-field checks
        if not email or not password:
            error = "Please enter both email and password."
        elif not role:
            error = "Please select a role."
        else:
            user = None

            # Look up in the right table based on role
            if role == "student":
                user = Student.objects.filter(email__iexact=email, password=password).first()
                if user:
                    request.session["user_role"] = "student"
                    request.session["user_id"] = user.id
                    return redirect("student_dashboard")

            elif role == "supervisor":
                user = Supervisor.objects.filter(email__iexact=email, password=password).first()
                if user:
                    request.session["user_role"] = "supervisor"
                    request.session["user_id"] = user.id
                    return redirect("supervisor_dashboard")

            elif role == "admin":
                user = Admin.objects.filter(email__iexact=email, password=password).first()
                if user:
                    request.session["user_role"] = "admin"
                    request.session["user_id"] = user.id
                    return redirect("admin_dashboard")

            # If we get here, login failed
            error = "Invalid email or password for the selected role."

    # GET request, or POST with error → show login again
    return render(request, "home.html", {"role": "guest", "error": error})


def student_dashboard(request):
    """
    Student dashboard:
    - Uses the logged-in student (from session)
    - Shows their name, email
    - Shows allocation status & allocated project (if any)
    """
     
    student = None
    allocated_project = None

    if request.session.get("user_role") == "student":
        student_id = request.session.get("user_id")
        student = Student.objects.filter(id= student_id).first()

        if student and student.allocated_project:
            allocated_project = student.allocated_project

    context = { 
        "role": "student",
        "student": student,
        "allocated_project": allocated_project,
    }        
    return render(request, "student_dashboard.html", context)


def student_profile(request):
    return render(request, "student_profile.html", {"role": "student"})


def student_projects(request):
    projects = Project.objects.select_related("supervisor").all()

    context = {
        "role": "student",
        "projects": projects,
    }
    return render(request, "student_projects.html", context)

def student_project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("supervisor"),
        id=project_id
    )

    context = {
        "role": "student",
        "project": project,
    }
    return render(request, "student_project_detail.html", context)

def student_preferences(request):
    return render(request, "student_preferences.html", {"role": "student"})


def supervisor_dashboard(request):
    return render(request, "supervisor_dashboard.html", {"role": "supervisor"})


def supervisor_projects(request):
    return render(request, "supervisor_projects.html", {"role": "supervisor"})


def supervisor_add_project(request):
    return render(request, "supervisor_add_project.html", {"role": "supervisor"})


def supervisor_interested_students(request):
    return render(request, "supervisor_interested_students.html", {"role": "supervisor"})


def admin_dashboard(request):
    return render(request, "admin_dashboard.html", {"role": "admin"})


def admin_students(request):
    return render(request, "admin_students.html", {"role": "admin"})


def admin_projects(request):
    return render(request, "admin_projects.html", {"role": "admin"})


def admin_supervisors(request):
    return render(request, "admin_supervisors.html", {"role": "admin"})


def admin_allocations(request):
    return render(request, "admin_allocations.html", {"role": "admin"})


def admin_manual_allocations(request):
    return render(request, "admin_manual_allocations.html", {"role": "admin"})
