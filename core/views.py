# app_name/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import (
    Student, Supervisor, Admin, Project,
    StudentProfileDetails, StudentModule, Module, Course,
    StudentPreference, AuditLog
)
from django.db.models import Count, Sum, F
from django.db.models.functions import Coalesce
from .forms import StudentProfileForm


def home(request):
    """
    Home = Login page.
    Uses real backend validation against Student / Supervisor / Admin tables.
    """
    error = None

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        # Basic empty-field checks
        if not email or not password:
            error = "Please enter both email and password."
        else:
            # Look up sequentially in Admin, Supervisor, then Student tables
            
            # Check Admin
            user = Admin.objects.filter(email__iexact=email).first()
            if user and user.check_password(password):
                request.session["user_role"] = "admin"
                request.session["user_id"] = user.id
                return redirect("admin_dashboard")
            
            # Check Supervisor
            user = Supervisor.objects.filter(email__iexact=email).first()
            if user and user.check_password(password):
                request.session["user_role"] = "supervisor"
                request.session["user_id"] = user.id
                return redirect("supervisor_dashboard")

            # Check Student
            user = Student.objects.filter(email__iexact=email).first()
            if user and user.check_password(password):
                request.session["user_role"] = "student"
                request.session["user_id"] = user.id
                return redirect("student_dashboard")

            # If we get here, login failed
            error = "Invalid email or password."

    # GET request, or POST with error → show login again
    return render(request, "home.html", {"role": "guest", "error": error})


def logout_view(request):
    """
    Logs out the user by completely flushing the session data.
    """
    request.session.flush()
    messages.success(request, "You have been successfully logged out.")
    return redirect("home")


def student_dashboard(request):
    """
    Student dashboard:
    - Uses the logged-in student (from session)
    - Shows their name, email
    - Shows allocation status & allocated project (if any)
    """
     
    student = None
    allocated_project = None
    pref_count = 0
    preferences_submitted = False

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
    
    # FEATURE: Locking System (Prevents modification of preferences after final submission)
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
        student.preferences_submitted_at = timezone.now()
        student.save()
        
        # Trigger Notification
        from .models import Notification, Admin
        Notification.objects.create(
            student_recipient=student,
            message="Your project preferences have been successfully submitted and locked.",
            link="/student/allocation/"
        )
        
        # Notify Admins
        admins = Admin.objects.all()
        for admin in admins:
            Notification.objects.create(
                admin_recipient=admin,
                message=f"Student {student.first_name} {student.last_name} has submitted their project preferences.",
                link=f"/admin-student/{student.id}/"
            )
            
        # Notify Supervisors of Ranked Projects
        ranked_prefs = StudentPreference.objects.filter(student=student, rank__gt=0).select_related('project__supervisor')
        supervisors_notified = set()
        for pref in ranked_prefs:
            supervisor = pref.project.supervisor
            if supervisor and supervisor.id not in supervisors_notified:
                Notification.objects.create(
                    supervisor_recipient=supervisor,
                    message=f"Student {student.first_name} {student.last_name} has submitted their preferences, which includes your project.",
                    link="/supervisor/interested-students/"
                )
                supervisors_notified.add(supervisor.id)
        
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

            # Audit Log for Profile Submission
            AuditLog.objects.create(
                user_description=f"Student ({student.email})",
                action="Profile Submitted" if "submit_profile" in request.POST else "Profile Draft Saved",
                details=f"Student Number: {profile.student_number}, Course: {profile.course}"
            )

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

import json
def ajax_update_preference_order(request):
    if request.method == "POST" and request.session.get("user_role") == "student":
        student = get_object_or_404(Student, id=request.session["user_id"])
        
        if student.preferences_submitted:
            return JsonResponse({"success": False, "error": "Preferences are locked."})

        try:
            data = json.loads(request.body)
            ordered_ids = data.get("ordered_ids", [])
            
            # First reset all current ranks to 0 for this student
            StudentPreference.objects.filter(student=student).update(rank=0)
            
            # Update the sorted ones with their new rank (1-indexed)
            for index, pref_id in enumerate(ordered_ids):
                StudentPreference.objects.filter(id=pref_id, student=student).update(rank=index + 1)
                
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request."})


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
            allocated_count=Count('allocated_students', distinct=True),
            interested_count=Count('studentpreference', distinct=True)
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
            
            # Audit Log for Project Addition
            AuditLog.objects.create(
                user_description=f"Supervisor ({supervisor.email})",
                action="Project Created",
                details=f"Title: {project.title}, Quota: {project.quota}"
            )
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
    
    if total_students > 0:
        total_allocations_percentage = (total_allocations / total_students) * 100
    else:
        total_allocations_percentage = 0
        
    total_preferences_submitted = Student.objects.filter(preferences_submitted=True).count()
    total_projects_added = Project.objects.count()
    
    # Calculate Seat Capacity (Filled vs Available Seats)
    from django.db.models import Sum
    total_seats_capacity = Project.objects.aggregate(total_seats=Sum('quota'))['total_seats'] or 0
    total_seats_filled = total_allocations
    total_seats_available = max(0, total_seats_capacity - total_seats_filled)

    # System Logs for Audit Trail
    system_logs = AuditLog.objects.all()[:15]

    return render(request, "admin_dashboard.html", {
        "role": "admin",
        "total_students": total_students,
        "total_projects": total_projects,
        "total_supervisors": total_supervisors,
        "total_allocations": total_allocations,
        "total_unallocated": total_unallocated,
        "total_allocations_percentage": round(total_allocations_percentage),
        "total_preferences_submitted": total_preferences_submitted,
        "total_projects_added": total_projects_added,
        "total_seats_filled": total_seats_filled,
        "total_seats_available": total_seats_available,
        "system_logs": system_logs
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
        allocated_count=Count('allocated_students', distinct=True),
        interested_count=Count('studentpreference', distinct=True)
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
    from django.db.models import OuterRef, Subquery, Sum
    from django.db.models.functions import Coalesce

    project_quota = Project.objects.filter(
        supervisor=OuterRef('pk')
    ).values('supervisor').annotate(
        total=Sum('quota')
    ).values('total')

    supervisors = Supervisor.objects.annotate(
        total_projects=Count('projects', distinct=True),
        total_allocated=Count('projects__allocated_students', distinct=True),
        total_interested=Count('projects__studentpreference__student', distinct=True),
        total_quota=Coalesce(Subquery(project_quota), 0)
    )

    # Calculate totals for the footer
    total_supervisors = 0
    total_projects = 0
    total_spaces_left = 0
    
    # Iterate to calculate load/status AND aggregate totals
    # We must do this before filtering if we want global totals, OR after if we want filtered totals.
    # The user's template implies they want totals for the displayed list.
    
    processed_supervisors = []
    
    for supervisor in supervisors:
        if supervisor.total_quota > 0:
            supervisor.load_percentage = (supervisor.total_allocated / supervisor.total_quota) * 100
        else:
            supervisor.load_percentage = 0

        if supervisor.total_allocated >= supervisor.total_quota and supervisor.total_quota > 0:
            supervisor.load_status = "Fully allocated"
            supervisor.load_class = "danger"
        elif supervisor.total_allocated > 0 and supervisor.total_quota > 0:
            supervisor.load_status = "Partially allocated"
            supervisor.load_class = "warning"
        else:
            supervisor.load_status = "Empty quota"
            supervisor.load_class = "success"    
        
        processed_supervisors.append(supervisor)

    # Apply Filters (in memory, since we have calculated fields)
    query = request.GET.get('q','').strip()
    if query:
        processed_supervisors = [
            s for s in processed_supervisors 
            if query.lower() in s.first_name.lower() or 
               query.lower() in s.last_name.lower() or 
               query.lower() in s.email.lower()
        ]
    
    load_filter = request.GET.get('load','').strip()
    if load_filter and load_filter != "All load levels":
        processed_supervisors = [s for s in processed_supervisors if s.load_status == load_filter]

    # Calculate Totals from the FINAL list
    total_supervisors = len(processed_supervisors)
    for s in processed_supervisors:
        total_projects += s.total_projects
        # Spaces left = Quota - Allocated (ensure non-negative)
        spaces = s.total_quota - s.total_allocated
        total_spaces_left += spaces if spaces > 0 else 0

    return render(request, "admin_supervisors.html", {
        "role": "admin",
        "supervisors": processed_supervisors,
        "search_query": query,
        "current_filter": load_filter,
        "total_supervisors_count": total_supervisors,
        "total_projects_count": total_projects,
        "total_spaces_left": total_spaces_left
    })


def admin_allocations(request):
    if request.session.get("user_role") != "admin":
        return redirect("home")
    if request.method == "POST":
        weight_preference = request.POST.get("weight_preference", 70)
        weight_academic = request.POST.get("weight_academic", 30)
        
        if "run_algo" in request.POST:
             from .utils import run_allocation_algorithm
             count = run_allocation_algorithm(weight_pref=weight_preference, weight_qual=weight_academic)
             
             if count > 0:
                 messages.success(request, f"Allocation complete! {count} students were newly allocated.")
                 log_action = "Success"
             else:
                 messages.info(request, "Algorithm ran, but no new allocations were made.")
                 log_action = "No Changes"
             
             # Audit Log for Fairness Engine
             AuditLog.objects.create(
                 user_description="Administrator",
                 action="Run Fairness Engine",
                 details=f"Result: {log_action}, New Allocations: {count}, Weights: Pref({weight_preference}) Qual({weight_academic})"
             )
                 
             return redirect("admin_allocations")

    total_students = Student.objects.count()
    allocated_count = Student.objects.filter(allocated_project__isnull=False).count()
    unallocated_count = total_students - allocated_count

    if total_students > 0:
        allocation_percentage = (allocated_count / total_students) * 100
    else:
        allocation_percentage = 0
    
    total_capacity = Project.objects.aggregate(total_capacity=Sum('quota'))['total_capacity'] or 0
    total_spaces_filled = allocated_count
    total_spaces_available = total_capacity - total_spaces_filled

    # 1. Unallocated Students (Profile done, Not allocated)
    # User feedback: School system has 2 chances. Manual allocation is for edge cases (forgot to submit etc).
    # So show ALL unallocated students, regardless of preferences submitted.
    unallocated_students = Student.objects.filter(
        allocated_project__isnull=True
    ).order_by('-preferences_submitted', 'last_name')

    from django.db.models import Count, Q, F
    stats = StudentPreference.objects.filter(
        project=F('student__allocated_project')
    ).aggregate(
        first_choices=Count('student', filter=Q(rank=1)),
        second_choices=Count('student', filter=Q(rank=2)),
        third_choices=Count('student', filter=Q(rank=3)),
    )

    return render(request, "admin_allocations.html", {
        "role": "admin",
        "total_students": total_students,
        "total_allocated": allocated_count,
        "total_unallocated": unallocated_count,
        "allocation_percentage": allocation_percentage,
        "total_capacity": total_capacity,
        "total_spaces_filled": total_spaces_filled,
        "total_spaces_available": total_spaces_available,
        "stats": stats,
        "unallocated_students": unallocated_students
    })


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


def admin_student_detail(request, student_id):
    if request.session.get("user_role") != "admin":
        return redirect("home")
    
    student = get_object_or_404(Student, id=student_id)
    profile = getattr(student, 'profile', None)
    
    # Get preferences with project details
    preferences = StudentPreference.objects.filter(student=student).select_related('project', 'project__supervisor').order_by('rank')
    
    return render(request, "admin_student_detail.html", {
        "role": "admin",
        "student": student,
        "profile": profile,
        "preferences": preferences
    })


def admin_project_detail(request, project_id):
    if request.session.get("user_role") != "admin":
        return redirect("home")

    project = get_object_or_404(Project, id=project_id)
    
    # Allocated Students
    allocated_students = project.allocated_students.all()
    
    # Interested Students (Preferences)
    interested_preferences = StudentPreference.objects.filter(project=project).select_related('student', 'student__profile').order_by('rank')
    
    # Calculate allocation percentage for progress bar
    allocation_percentage = 0
    if project.quota > 0:
        count = allocated_students.count()
        allocation_percentage = int((count / project.quota) * 100)

    return render(request, "admin_project_detail.html", {
        "role": "admin",
        "project": project,
        "allocated_students": allocated_students,
        "interested_preferences": interested_preferences,
        "allocation_percentage": allocation_percentage
    })


def student_allocation(request):
    if request.session.get("user_role") != "student":
        return redirect("home")
    
    student = get_object_or_404(Student, id=request.session["user_id"])
    
    context = {
        "role": "student",
        "student": student,
        "is_allocated": False,
        "allocated_project": None,
        "supervisor": None,
        "rank": None,
        "preferences": [],
        "alternatives": []
    }
    
    if student.allocated_project:
        context["is_allocated"] = True
        context["allocated_project"] = student.allocated_project
        context["supervisor"] = student.allocated_project.supervisor
        
        # Find which rank this was
        try:
            pref = StudentPreference.objects.get(student=student, project=student.allocated_project)
            if pref.rank == 1: context["rank"] = "1st"
            elif pref.rank == 2: context["rank"] = "2nd"
            elif pref.rank == 3: context["rank"] = "3rd"
            else: context["rank"] = f"{pref.rank}th"
            
        except StudentPreference.DoesNotExist:
            context["rank"] = "Manually Assigned"
            
    else:
        # Not Allocated Logic
        from .utils import calculate_prerequisite_match
        
        # 1. Get their preferences and annotate with status
        prefs = StudentPreference.objects.filter(student=student).order_by('rank')
        pref_data = []
        
        # Helper to check if project full
        projects = Project.objects.annotate(current_allocations=Count('allocated_students'))
        states = {p.id: {'filled': p.current_allocations, 'quota': p.quota} for p in projects}
        
        for p in prefs:
            proj = p.project
            s = states.get(proj.id, {'filled':0, 'quota':0})
            is_full = s['filled'] >= s['quota']
            
            pref_data.append({
                "rank": p.rank,
                "project": proj,
                "status": "Filled" if is_full else "Criteria Mismatch" 
            })
        context["preferences"] = pref_data
        
        # 2. Find Alternatives (Projects with space + >0 criteria match)
        # Get all projects with space
        all_projects_with_space = [p for p in projects if p.current_allocations < p.quota]
        
        alternatives = []
        # Get profile skills safely
        skills = ""
        try:
             skills = student.profile.skills
        except StudentProfileDetails.DoesNotExist:
             pass

        for proj in all_projects_with_space:
            matches, _ = calculate_prerequisite_match(skills, proj.prerequisites)
            if matches > 0:
                alternatives.append(proj)
                if len(alternatives) >= 3: break # Limit to 3 suggestions
        
        context["alternatives"] = alternatives

    return render(request, "student_allocation.html", context)


def admin_allocation_results(request):
    if request.session.get("user_role") != "admin":
        return redirect("home")
    
    # optimize query
    students = Student.objects.select_related('allocated_project', 'allocated_project__supervisor').all().order_by('last_name')
    
    # We want to show rank if allocated
    # This might be N+1 if we iterate, but we can pre-fetch preferences
    # Or just do a simple lookup in template if we pass a dict.
    # Let's annotate or just build a list.
    
    student_data = []
    for s in students:
        rank = "-"
        if s.allocated_project:
            # Try to start with "Manual"
            rank = "Manual"
            # check preference
            # (Inefficient in loop, but okay for <100 students. For production, use prefetch_related)
            try:
                p = StudentPreference.objects.get(student=s, project=s.allocated_project)
                rank = p.rank
            except StudentPreference.DoesNotExist:
                pass
        
        student_data.append({
            "student": s,
            "allocated_project": s.allocated_project,
            "supervisor": s.allocated_project.supervisor if s.allocated_project else None,
            "rank": rank
        })
            
    return render(request, "admin_allocation_results.html", {
        "student_data": student_data,
        "role": "admin"
    })


def admin_manual_allocations(request):
    if request.session.get("user_role") != "admin":
        return redirect("home")
    
    if request.method == "POST":
        student_id = request.POST.get("student")
        project_id = request.POST.get("project")
        
        if student_id and project_id:
            student = get_object_or_404(Student, id=student_id)
            project = get_object_or_404(Project, id=project_id)
            
            # Check if student is already in this project
            if student.allocated_project == project:
                messages.info(request, f"{student} is already allocated to {project.title}.")
                return redirect("admin_manual_allocations")

            # Verify project has space
            if project.quota > project.allocated_students.count():
                old_project = student.allocated_project
                student.allocated_project = project
                student.save()
                
                # Trigger Notifications
                from .models import Notification
                if old_project:
                    Notification.objects.create(
                        supervisor_recipient=old_project.supervisor,
                        message=f"Admin reallocated {student.first_name} {student.last_name} away from your project: {old_project.title}",
                        link=f"/supervisor/dashboard/"
                    )
                    
                Notification.objects.create(
                    student_recipient=student,
                    message=f"You have been manually allocated to project: {project.title}",
                    link="/student/allocation/"
                )
                Notification.objects.create(
                    supervisor_recipient=project.supervisor,
                    message=f"Admin manually assigned {student.first_name} {student.last_name} to your project: {project.title}",
                    link=f"/supervisor/project/{project.id}/"
                )
                
                messages.success(request, f"Successfully allocated {student} to {project.title}")
                
                # Audit Log for Manual Allocation
                AuditLog.objects.create(
                    user_description="Administrator",
                    action="Manual Allocation",
                    details=f"Assigned {student.email} to project: {project.title}"
                )
            else:
                messages.error(request, f"{project.title} has reached its quota limit.")
        else:
            messages.error(request, "Please select both a student and a project.")
            
        return redirect("admin_manual_allocations")

    # GET: Prepare Lists
    
    # 1. All Students
    # Including already allocated students so the admin can re-allocate them as an edge case.
    all_students = Student.objects.select_related('allocated_project').all().order_by('allocated_project', '-preferences_submitted', 'last_name')
    
    # 2. Available Projects (Quota > Count)
    # Annotate with count
    available_projects = Project.objects.annotate(
        allocation_count=Count('allocated_students')
    ).filter(allocation_count__lt=F('quota')).order_by('title')
    
    return render(request, "admin_manual_allocations.html", {
        "role": "admin",
        "all_students": all_students,
        "available_projects": available_projects
    })


def admin_notify_students(request):
    if request.session.get("user_role") != "admin":
        return redirect("home")
        
    if request.method == "POST":
        from .models import Student, Notification
        
        students = Student.objects.select_related('allocated_project', 'profile').all()
        count = 0
        for student in students:
            link = "/student/dashboard/"
            if student.allocated_project:
                 msg = "If you have been allocated a project, you will see your supervisor and project title on your dashboard."
            else:
                 has_profile = False
                 try:
                     has_profile = student.profile.profile_status == "SUBMITTED"
                 except Exception:
                     pass
                 
                 has_prefs = student.preferences_submitted
                 
                 if not has_profile or not has_prefs:
                     msg = "kindly fill and or submit your profile and preference"
                     link = "/student/profile/"
                 else:
                     msg = "If you are currently unallocated, please log in to review available projects or contact the module team."
                     link = "/student-projects/"
                     
            Notification.objects.create(
                student_recipient=student,
                message=msg,
                link=link
            )
            count += 1
            
        messages.success(request, f"Successfully sent notifications to {count} students.")
        
    return redirect("admin_allocations")


def mark_notifications_read(request):
    """Marks all unread notifications for the current user as read."""
    if request.method == "POST":
        user_id = request.session.get("user_id")
        user_role = request.session.get("user_role")

        if user_id and user_role:
            from .models import Notification
            if user_role == "student":
                Notification.objects.filter(student_recipient_id=user_id, is_read=False).update(is_read=True)
            elif user_role == "supervisor":
                Notification.objects.filter(supervisor_recipient_id=user_id, is_read=False).update(is_read=True)
            elif user_role == "admin":
                Notification.objects.filter(admin_recipient_id=user_id, is_read=False).update(is_read=True)

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect("home")

import csv
from django.http import HttpResponse

def admin_export_data(request):
    """Exports allocations to a CSV file including rank and rationale."""
    if request.session.get("user_role") != "admin":
        return redirect("home")
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="allocations_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Student Email', 'Allocated Project', 'Supervisor', 'Preference Rank', 'Allocation Rationale'])
    
    from .models import Student, StudentPreference
    students = Student.objects.select_related('allocated_project', 'allocated_project__supervisor').all().order_by('last_name')
    
    for s in students:
        if s.allocated_project:
            rank = "Manual"
            rationale = "Manually allocated by Administrator."
            try:
                p = StudentPreference.objects.get(student=s, project=s.allocated_project)
                rank = p.rank
                
                if rank == 1:
                    rationale = "Rank 1 Preference - Highest overall hybrid score."
                elif rank > 1:
                    # Determine why they got rank > 1. Was Rank 1 full, or did Rank 2 just have a better score?
                    # We can check the Rank 1 project's current allocation count.
                    higher_prefs = StudentPreference.objects.filter(student=s, rank__lt=rank)
                    was_full = False
                    for hp in higher_prefs:
                        if hp.project.allocated_students.count() >= hp.project.quota:
                            was_full = True
                            
                    if was_full:
                        rationale = f"Rank {rank} Preference - Cascaded because higher preference was at maximum quota."
                    else:
                        rationale = f"Rank {rank} Preference - Assigned due to significantly higher academic profile match overriding preference rank."
                        
            except StudentPreference.DoesNotExist:
                pass
            
            project_title = s.allocated_project.title
            supervisor_name = f"{s.allocated_project.supervisor.first_name} {s.allocated_project.supervisor.last_name}"
        else:
            project_title = "Unallocated"
            supervisor_name = "N/A"
            rank = "N/A"
            rationale = "No successful match found or unallocated."
            
        writer.writerow([
            f"{s.first_name} {s.last_name}",
            s.email,
            project_title,
            supervisor_name,
            rank,
            rationale
        ])
        
    return response
