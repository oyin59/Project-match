# app_name/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import (
    Student, Supervisor, Admin, Project,
    StudentProfileDetails, StudentModule, Module, Course,
    StudentPreference
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
        student = Student.objects.filter(id=student_id).first()

        if student:
            if student.allocated_project:
                allocated_project = student.allocated_project
            
            # Count selected preferences
            from .models import StudentPreference
            pref_count = StudentPreference.objects.filter(student=student).count()
            preferences_submitted = student.preferences_submitted

    context = { 
        "role": "student",
        "student": student,
        "allocated_project": allocated_project,
        "pref_count": pref_count,
        "preferences_submitted": preferences_submitted,
    }        
    return render(request, "student_dashboard.html", context)




def ajax_load_courses(request):
    department_id = request.GET.get("department_id")
    courses = Course.objects.filter(department_id=department_id).values("id", "name")
    return JsonResponse(list(courses), safe=False)


def ajax_load_modules(request):
    course_id = request.GET.get("course_id")
    modules = Module.objects.filter(course_id=course_id).values("id", "code", "name")
    return JsonResponse(list(modules), safe=False)



def student_projects(request):
    if request.session.get("user_role") != "student":
        return redirect("home")
        
    student = get_object_or_404(Student, id=request.session["user_id"])
    
    # Base Query
    projects = Project.objects.select_related("supervisor").all()
    
    # 1. Search (Title or Description)
    query = request.GET.get('q', '').strip()
    if query:
        from django.db.models import Q
        projects = projects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )
        
    # 2. Filter by Supervisor
    supervisor_id = request.GET.get('supervisor')
    if supervisor_id and supervisor_id.isdigit():
        projects = projects.filter(supervisor_id=int(supervisor_id))
        
    # Get all supervisors for the dropdown
    all_supervisors = Supervisor.objects.all().order_by('last_name')
    
    # Get current student's selected project IDs
    selected_project_ids = StudentPreference.objects.filter(student=student).values_list("project_id", flat=True)
    pref_count = len(selected_project_ids)

    context = {
        "role": "student",
        "projects": projects,
        "all_supervisors": all_supervisors,
        "selected_project_ids": list(selected_project_ids),
        "pref_count": pref_count,
        "preferences_submitted": student.preferences_submitted,
        "current_search": query,
        "current_supervisor": int(supervisor_id) if supervisor_id and supervisor_id.isdigit() else None
    }
    return render(request, "student_projects.html", context)


def student_add_preference(request, project_id):
    if request.session.get("user_role") != "student":
        return redirect("home")
    
    student = get_object_or_404(Student, id=request.session["user_id"])
    
    # LOCK: Cannot add if submitted
    if student.preferences_submitted:
        messages.error(request, "Preferences are locked. You cannot add projects after creating a submission.")
        return redirect("student_projects")

    project = get_object_or_404(Project, id=project_id)
    
    # Check if already in preferences
    if StudentPreference.objects.filter(student=student, project=project).exists():
        return redirect("student_projects")
    
    # Check if already has 3 preferences
    current_count = StudentPreference.objects.filter(student=student).count()
    if current_count >= 3:
        return redirect("student_projects")
    
    # Add new preference as UNRANKED (rank=0)
    StudentPreference.objects.create(
        student=student,
        project=project,
        rank=0
    )
    
    return redirect("student_projects")

def student_project_detail(request, project_id):
    if request.session.get("user_role") != "student":
        return redirect("home")

    project = get_object_or_404(Project, id=project_id)
    return render(request, "student_project_detail.html", {
        "role": "student",
        "project": project
    })


def student_preferences(request):
    if request.session.get("user_role") != "student":
        return redirect("home")

    student = get_object_or_404(Student, id=request.session["user_id"])
    print(f"DEBUG: student_preferences view accessed. User: {student.email}, preferences_submitted: {student.preferences_submitted}")
    
    # Get user preferences
    preferences = StudentPreference.objects.filter(student=student).select_related("project", "project__supervisor").order_by("rank")

    # SELF-HEALING: If marked submitted but has NO preferences, it's an invalid state. Unlock it.
    if student.preferences_submitted and preferences.count() == 0:
        print(f"DEBUG: Auto-correcting invalid state for {student.email} (Submitted=True but count=0)")
        student.preferences_submitted = False
        student.save()

    return render(request, "student_preferences.html", {
        "role": "student",
        "preferences": preferences,
        "preferences_submitted": student.preferences_submitted
    })

def student_save_draft(request):
    """
    Explicitly saves draft (visual feedback only since DB is always up to date).
    """
    if request.session.get("user_role") != "student":
        return redirect("home")
        
    student = get_object_or_404(Student, id=request.session["user_id"])
    if student.preferences_submitted:
         messages.info(request, "Your preferences are already submitted.")
    else:
         messages.success(request, "Preferences saved as draft.")
         
    return redirect("student_preferences")


def student_remove_preference(request, preference_id):
    if request.session.get("user_role") != "student":
        return redirect("home")
    
    student = get_object_or_404(Student, id=request.session["user_id"])
    
    # LOCK: Cannot remove if submitted
    if student.preferences_submitted:
        messages.error(request, "Preferences are locked. You cannot remove projects after submission.")
        return redirect("student_preferences")

    preference = get_object_or_404(StudentPreference, id=preference_id, student=student)
    preference.delete()
    
    # Re-rank ONLY the remaining RANKED preferences
    # Filter for rank__gt=0 to exclude unranked items
    ranked_remaining = StudentPreference.objects.filter(student=student, rank__gt=0).order_by("rank")
    for i, pref in enumerate(ranked_remaining):
        # Assign new rank starting from 1
        pref.rank = i + 1
        pref.save()
        
    return redirect("student_preferences")


def student_submit_preferences(request):
    """
    Finalizes the student's preferences.
    """
# ... implementation continues below ...
    """
    Finalizes the student's preferences.
    """
    if request.session.get("user_role") != "student":
        return redirect("home")
    
    if request.method == "POST":
        student = get_object_or_404(Student, id=request.session["user_id"])
        
        # Check if they have at least 1 preference? 
        count = StudentPreference.objects.filter(student=student).count()
        if count == 0:
            messages.error(request, "You must select at least one project before submitting.")
            return redirect("student_preferences")
            
        student.preferences_submitted = True
        student.save()
        
        messages.success(request, "Your preferences have been successfully submitted!")
        return redirect("student_dashboard")
        
    return redirect("student_preferences")

def student_profile(request):
    if request.session.get("user_role") != "student":
        return redirect("home")

    student = Student.objects.get(id=request.session["user_id"])
    print(f"DEBUG: student_profile view accessed. User: {student.email}, Initial preferences_submitted: {student.preferences_submitted}")
    profile, _ = StudentProfileDetails.objects.get_or_create(student=student)
    modules_qs = Module.objects.none()
    if profile.course_id:
        modules_qs = Module.objects.filter(course_id=profile.course_id).order_by("code")


    if request.method == "POST":
        form = StudentProfileForm(request.POST, instance=profile)

        if form.is_valid():
            profile = form.save(commit=False)

            if "submit_profile" in request.POST:
                print(f"DEBUG: PROFILE SUBMITTED via POST for {student.email}")
                profile.profile_status = "SUBMITTED"
                # Note: User requested separate submissions, so we don't auto-submit preferences here anymore
                # unless explicitly desired. The previous code did: student.preferences_submitted = True
                # I will REMOVE that side-effect to keep them distinct as requested.
                # I will REMOVE that side-effect to keep them distinct as requested.
                # student.save()
                print(f"DEBUG: Saved profile. preferences_submitted is now: {student.preferences_submitted}")
                messages.success(request, "Profile submitted successfully!")

            profile.save()

            StudentModule.objects.filter(student=student).delete()
            for module_id in request.POST.getlist("modules"):
                StudentModule.objects.create(
                    student=student,
                    module_id=module_id
                )
            
            if "submit_profile" not in request.POST:
                 messages.success(request, "Profile draft saved.")
                 return redirect("student_profile")

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


def student_reorder_preference(request, preference_id, direction):
    if request.session.get("user_role") != "student":
        return redirect("home")
    
    student = get_object_or_404(Student, id=request.session["user_id"])
    
    # LOCK: Cannot reorder if submitted
    if student.preferences_submitted:
        messages.error(request, "Preferences are locked. You cannot reorder projects after submission.")
        return redirect("student_preferences")
        
    preference = get_object_or_404(StudentPreference, id=preference_id, student=student)
    
    # If starting rank is 0, give it the next available rank
    if preference.rank == 0:
        if direction == "up":
             # Find max rank used so far
             from django.db.models import Max
             max_rank = StudentPreference.objects.filter(student=student).aggregate(Max('rank'))['rank__max'] or 0
             preference.rank = max_rank + 1
             preference.save()
        # 'down' on unranked doesn't really mean anything
        return redirect("student_preferences")


    # Standard reorder for ranked items
    current_rank = preference.rank
    if direction == "up" and current_rank > 1:
        # Move Up: swap with rank-1
        # BUT we must ensure the item at rank-1 exists
        other = StudentPreference.objects.filter(student=student, rank=current_rank - 1).first()
        if other:
            preference.rank -= 1
            other.rank += 1
            preference.save()
            other.save()
            
    elif direction == "down":
        # Move Down: swap with rank+1
        other = StudentPreference.objects.filter(student=student, rank=current_rank + 1).first()
        if other:
            preference.rank += 1
            other.rank -= 1
            preference.save()
            other.save()
        else:
            # If no item below, moving down returns to unranked (rank 0)?
            # Or just stays at bottom? User said "they are now able to rank it by themselves",
            # implies dragging from unranked pool up to ranked list.
            # Let's assume moving down from bottom simply makes it unranked again.
            preference.rank = 0
            preference.save()
        
    return redirect("student_preferences")


def supervisor_dashboard(request):
    if request.session.get("user_role") != "supervisor":
        return redirect("home")

    supervisor_id = request.session.get("user_id")
    supervisor = get_object_or_404(Supervisor, id=supervisor_id)

    from django.db.models import Sum, Count

    # Calculate Interested Students (Distinct count)
    interested_student_count = StudentPreference.objects.filter(project__supervisor=supervisor).values("student").distinct().count()

    return render(request, "supervisor_dashboard.html", {
        "role": "supervisor",
        "supervisor": supervisor,
        "projects": supervisor.projects.annotate(
            allocated_count=Count('allocated_students'),
            interested_count=Count('studentpreference')
        ),
        "total_projects": supervisor.projects.count(),
        "total_quota": supervisor.projects.aggregate(Sum('quota'))['quota__sum'] or 0,
        "total_allocated": supervisor.projects.aggregate(
            total=Count('allocated_students')
        )['total'] or 0,
        "interested_student_count": interested_student_count,
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
    if request.session.get("user_role") != "supervisor":
        return redirect("home")

    supervisor_id = request.session.get("user_id")
    supervisor = get_object_or_404(Supervisor, id=supervisor_id)
    
    # Get all projects for filter dropdown
    projects = supervisor.projects.all()
    
    # Base Query: Preferences for this supervisor's projects
    preferences = StudentPreference.objects.filter(
        project__supervisor=supervisor
    ).select_related('student', 'project', 'student__profile').order_by('project', 'rank')
    
    # Global Stats
    total_projects_count = projects.count()
    
    # Default Summary (All Projects)
    summary_interested = StudentPreference.objects.filter(project__supervisor=supervisor).values('student').distinct().count()
    summary_quota = "Varies"
    summary_projects_count = total_projects_count
    summary_allocated = Student.objects.filter(allocated_project__supervisor=supervisor).order_by('first_name')
    
    selected_project = None

    # Filter by Project
    selected_project_id = request.GET.get('project')
    if selected_project_id and selected_project_id.isdigit():
        project_id = int(selected_project_id)
        # Verify project belongs to supervisor
        selected_project = projects.filter(id=project_id).first()
        
        if selected_project:
            # Filter preferences
            preferences = preferences.filter(project_id=project_id)
            
            # Update Summary for specific project
            summary_interested = preferences.count()
            summary_quota = selected_project.quota
            summary_allocated = selected_project.allocated_students.all()
    
    # Calculate Prerequisite Matches
    from .utils import calculate_prerequisite_match
    
    # Evaluate queryset to list to attach attributes
    # (Or keep as queryset and attach in template tag? No, user requested "Call this function per student-project pair" in backend)
    # Iterate and attach
    # Creating a list of wrappers or just attaching to model instances works for read-only view.
    # We will fetch all first since we need to iterate.
    # Note: 'preferences' was already a queryset.
    
    # Check if student has profile, handle exceptions if 'profile' doesn't exist (though our query does select_related)
    # But select_related('student__profile') might fail if it's a specific reverse relation name or OneToOne?
    # Model: student = models.OneToOneField(Student, related_name="profile") -> Access via student.profile
    # However, if profile doesn't exist, accessing it raises specific Error unless we handle it.
    # Let's be safe.
    
    preferences_list = []
    for pref in preferences:
        try:
            skills = pref.student.profile.skills
        except StudentProfileDetails.DoesNotExist:
            skills = ""
            
        pref.match_data = calculate_prerequisite_match(skills, pref.project.prerequisites)
        preferences_list.append(pref)

    return render(request, "supervisor_interested_students.html", {
        "role": "supervisor",
        "preferences": preferences_list,
        "projects": projects,
        "selected_project_id": int(selected_project_id) if selected_project_id and selected_project_id.isdigit() else None,
        "summary_interested": summary_interested,
        "summary_quota": summary_quota,
        "summary_projects_count": summary_projects_count,
        "summary_allocated": summary_allocated
    })


def admin_dashboard(request):
    if request.session.get("user_role") != "admin":
        return redirect("home")
    admin_id = request.session.get("user_id")
    admin = get_object_or_404(Admin, id=admin_id)
    total_students = Student.objects.count()
    total_projects = Project.objects.count()
    total_supervisors = Supervisor.objects.count()
    total_allocations = Student.objects.filter(allocated_project__isnull=False).count()
    total_unallocated = Student.objects.filter(allocated_project__isnull=True).count()
    total_allocations_percentage = (total_allocations / total_students) * 100
    total_preferences_submitted = Student.objects.filter(preferences_submitted=True).count()
    total_projects_added = Project.objects.count()
    return render(request, "admin_dashboard.html", {"role": "admin",
    "total_students": total_students,
    "total_projects": total_projects,
    "total_supervisors": total_supervisors,
    "total_allocations": total_allocations,
    "total_unallocated": total_unallocated,
    "total_allocations_percentage": total_allocations_percentage,
    "total_preferences_submitted": total_preferences_submitted,
    "total_projects_added": total_projects_added
    })


def admin_students(request):
    if request.session.get("user_role") != "admin":
        return redirect("home")
    students = Student.objects.select_related('allocated_project', 'profile').prefetch_related('preferences__project').all().order_by('last_name')
    query = request.GET.get('q','').strip()
    if query:
        from django.db.models.functions import Q
        students = students.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
            )
    status_filter = request.GET.get('status','All students')
    if status_filter == 'Allocated':
        students = students.filter(allocated_project__isnull=False)
    elif status_filter == 'Unallocated':
        students = students.filter(allocated_project__isnull=True)
    elif status_filter == 'No preferences':
        students = students.filter(preferences_submitted=False)

    for student in students:
        # Access preferences via the prefetched RELATIONSHIP on the INSTANCE
        # Because of prefetch_related('preferences__project'), this doesn't hit DB again
        prefs = list(student.preferences.all()) 
        prefs.sort(key=lambda x: x.rank)
        
        # Assign attributes to the INSTANCE, not the Class
        student.pref_1 = prefs[0].project.title if len(prefs) > 0 else "-"
        student.pref_2 = prefs[1].project.title if len(prefs) > 1 else "-"
        student.pref_3 = prefs[2].project.title if len(prefs) > 2 else "-"

    return render(request, "admin_students.html", {
        "role": "admin",
        "students": students,
        "search_query": query,
        "current_filter": status_filter,
        })


def admin_projects(request):
    if request.session.get("user_role") != "admin":
        return redirect("home")
    projects = Project.objects.select_related('supervisor').annotate(
        allocated_count=Count('allocated_students'),
        interested_count=Count('studentpreference')
    ).order_by('title')
    query = request.GET.get('q','').strip()
    if query:
        projects = projects.filter(title__icontains=query)
    supervisor_filter = request.GET.get('supervisor','All supervisors')
    if supervisor_filter != 'All supervisors':
        if supervisor_filter.isdigit():
            projects = projects.filter(supervisor__id=int(supervisor_filter))
        else:
            projects = projects.filter(
                Q(supervisor__first_name__icontains=supervisor_filter) |
                Q(supervisor__last_name__icontains=supervisor_filter)
            )
    status_filter = request.GET.get('status','All status')

    from django.db.models import F

    if status_filter == 'Fully filled':
        projects = projects.filter(allocated_count__gte=F('quota'))
    elif status_filter == 'Partially filled':
        projects = projects.filter(allocated_count__gt=0, allocated_count__lt=F('quota'))
    elif status_filter == 'Spaces available':
        projects = projects.filter(allocated_count__lt=F('quota'))

    total_count = projects.count()

    for project in projects:
        if project.allocated_count >= project.quota:
            project.status = 'Fully filled'
            project.status_class = 'danger'
        elif project.allocated_count > 0:
            project.status = 'Partially filled'
            project.status_class = 'warning'
        else:
            project.status = 'Spaces available'
            project.status_class = 'success'

    all_supervisors = Supervisor.objects.all().order_by('last_name')
    return render(request, "admin_projects.html", {
        "role": "admin",
        "projects": projects,
        "all_supervisors": all_supervisors,
        "search_query": query,
        "current_supervisor": supervisor_filter,
        "current_status": status_filter,
        "total_count": total_count,
        })


def admin_supervisors(request):
    if request.session.get("user_role") != "admin":
        return redirect("home")
    return render(request, "admin_supervisors.html", {"role": "admin"})


def admin_allocations(request):
    if request.session.get("user_role") != "admin":
        return redirect("home")
    return render(request, "admin_allocations.html", {"role": "admin"})


def admin_manual_allocations(request):
    if request.session.get("user_role") != "admin":
        return redirect("home")
    return render(request, "admin_manual_allocations.html", {"role": "admin"})


def admin_export_data(request):
    import csv 
    from django.http import HttpResponse
    
    if request.session.get("user_role") != "admin":
        return redirect("home")
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="allocation_data.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Student Email', 'Allocated Project', 'Supervisor', 'Preferences Submitted'])
    
    students = Student.objects.select_related('allocated_project', 'allocated_project__supervisor').all()
    
    for student in students:
        project_title = student.allocated_project.title if student.allocated_project else "Unallocated"
        supervisor_name = str(student.allocated_project.supervisor) if student.allocated_project else "-"
        
        writer.writerow([
            str(student),
            student.email,
            project_title,
            supervisor_name,
            "Yes" if student.preferences_submitted else "No"
        ])
        
    return response
