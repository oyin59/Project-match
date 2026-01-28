# app_name/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import (
    Student, Supervisor, Admin, Project,
    StudentProfileDetails, StudentModule, Module, Course
)
from django.db.models import Count, Sum
from .forms import StudentProfileForm


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
    if request.session.get("user_role") != "student":
        return redirect("home")

    student = Student.objects.get(id=request.session["user_id"])
    profile, _ = StudentProfileDetails.objects.get_or_create(student=student)
    modules_qs = Module.objects.none()
    if profile.course_id:
        modules_qs = Module.objects.filter(course_id=profile.course_id).order_by("code")


    if request.method == "POST":
        form = StudentProfileForm(request.POST, instance=profile)

        if form.is_valid():
            profile = form.save(commit=False)

            if "submit_profile" in request.POST:
                profile.profile_status = "SUBMITTED"
                student.preferences_submitted = True
                student.save()

            profile.save()

            StudentModule.objects.filter(student=student).delete()
            for module_id in request.POST.getlist("modules"):
                StudentModule.objects.create(
                    student=student,
                    module_id=module_id
                )

            return redirect("student_dashboard")
    else:
        form = StudentProfileForm(instance=profile)

    selected_modules = StudentModule.objects.filter(
        student=student
    ).values_list("module_id", flat=True)

    return render(request, "student_profile.html", {
        "role": "student",
        "form": form,
        "modules": modules_qs,
        "selected_modules": list(selected_modules),
    })

def ajax_load_courses(request):
    department_id = request.GET.get("department_id")
    courses = Course.objects.filter(department_id=department_id).values("id", "name")
    return JsonResponse(list(courses), safe=False)


def ajax_load_modules(request):
    course_id = request.GET.get("course_id")
    modules = Module.objects.filter(course_id=course_id).values("id", "code", "name")
    return JsonResponse(list(modules), safe=False)



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
    if request.session.get("user_role") != "supervisor":
        return redirect("home")

    supervisor_id = request.session.get("user_id")
    supervisor = get_object_or_404(Supervisor, id=supervisor_id)

    from django.db.models import Sum, Count

    return render(request, "supervisor_dashboard.html", {
        "role": "supervisor",
        "supervisor": supervisor,
        "projects": supervisor.projects.annotate(
            allocated_count=Count('allocated_students')
        ),
        "total_projects": supervisor.projects.count(),
        "total_quota": supervisor.projects.aggregate(Sum('quota'))['quota__sum'] or 0,
        "total_allocated": supervisor.projects.aggregate(
            total=Count('allocated_students')
        )['total'] or 0,
        "recent_projects": supervisor.projects.order_by('-created_at')[:5]
    })


def supervisor_projects(request):
    if request.session.get("user_role") != "supervisor":
        return redirect("home")

    supervisor_id = request.session.get("user_id")
    supervisor = get_object_or_404(Supervisor, id=supervisor_id)
    
    projects = supervisor.projects.annotate(
        allocated_count=Count('allocated_students')
    )

    return render(request, "supervisor_projects.html", {
        "role": "supervisor",
        "projects": projects
    })

def supervisor_project_detail(request, project_id):
    if request.session.get("user_role") != "supervisor":
        return redirect("home")

    supervisor_id = request.session.get("user_id")
    project = get_object_or_404(Project, id=project_id, supervisor_id=supervisor_id)
    
    # Calculate stats for detail page if needed
    project.allocated_count = project.allocated_students.count()

    return render(request, "supervisor_project_detail.html", {
        "role": "supervisor",
        "project": project
    })


from .forms import StudentProfileForm, ProjectForm

def supervisor_add_project(request):
    if request.session.get("user_role") != "supervisor":
        return redirect("home")

    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            supervisor_id = request.session.get("user_id")
            project.supervisor = get_object_or_404(Supervisor, id=supervisor_id)
            project.save()
            return redirect("supervisor_dashboard")
    else:
        form = ProjectForm()

    return render(request, "supervisor_add_project.html", {
        "role": "supervisor",
        "form": form
    })

def supervisor_edit_project(request, project_id):
    if request.session.get("user_role") != "supervisor":
        return redirect("home")

    supervisor_id = request.session.get("user_id")
    project = get_object_or_404(Project, id=project_id, supervisor_id=supervisor_id)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("supervisor_dashboard")
    else:
        form = ProjectForm(instance=project)

    return render(request, "supervisor_add_project.html", {
        "role": "supervisor",
        "form": form,
        "is_edit": True,
        "project": project
    })


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
