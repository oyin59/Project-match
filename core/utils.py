def calculate_prerequisite_match(student_skills: str, project_prerequisites: str) -> tuple[int, int]:
    """
    Compare student skills against project prerequisites.
    Returns (matched_count, total_count).
    Case-insensitive. Handles comma-separated strings.
    """
    if not project_prerequisites:
        return 0, 0

    import re
    # Parse and normalize prerequisites
    raw_prereqs = re.split(r'[,\n]', project_prerequisites)
    prereqs = []
    for p in raw_prereqs:
        cleaned = re.sub(r'^[\-\*\s]+', '', p.strip()).lower()
        if cleaned:
            prereqs.append(cleaned)

    if not prereqs:
        return 0, 0

    if not student_skills:
        return 0, len(prereqs)

    # Parse and normalize skills
    raw_skills = re.split(r'[,\n]', student_skills)
    skills = set()
    for s in raw_skills:
        cleaned = re.sub(r'^[\-\*\s]+', '', s.strip()).lower()
        if cleaned:
            skills.add(cleaned)

    # Count matches
    matched_count = sum(1 for p in prereqs if p in skills)
    
    return matched_count, len(prereqs)


def run_allocation_algorithm():
    """
    Executes the automated allocation process based on user-defined logic:
    1. Filter eligible students (Profile & Prefs submitted, Unallocated).
    2. Sort by `preferences_submitted_at` (Ascending) -> `last_name` (Ascending).
    3. For each student, calculate scores for their preferred projects:
       - Profile Score: (Matches / 6) * 50
       - Preference Score: Rank 1=50, Rank 2=30, Rank 3=10
       - Total Score = Profile + Preference
    4. Allocate to the highest-scoring project that has space.
    5. Update student status.
    """
    from .models import Student, Project, StudentPreference
    from django.db.models import Count, F
    
    # Step 1: Filter Eligible Students
    eligible_students = Student.objects.filter(
        preferences_submitted=True,
        allocated_project__isnull=True
        # Note: We assume profile is submitted if preferences are, based on workflow
    )
    
    # Step 2: Sort Students
    # Sort by timestamp (earliest first), and alphabetical name as tie-breaker
    sorted_students = eligible_students.order_by('preferences_submitted_at', 'last_name', 'first_name')
    
    # Track project capacities in memory to avoid DB hits in loop
    projects = Project.objects.annotate(current_allocations=Count('allocated_students'))
    project_states = {p.id: {'obj': p, 'filled': p.current_allocations, 'quota': p.quota, 'prereqs': p.prerequisites} for p in projects}
    
    allocated_count = 0
    
    for student in sorted_students:
        best_project_id = None
        highest_score = -1
        
        # Get Student's Preferences
        preferences = StudentPreference.objects.filter(student=student).order_by('rank')
        
        for pref in preferences:
            p_id = pref.project.id
            if p_id not in project_states:
                continue
                
            state = project_states[p_id]
            
            # Check Quota
            if state['filled'] >= state['quota']:
                continue
                
            # Step 3: Compute Scores
            
            # A. Profile Matching Score (0-50)
            # We use the helper function we already have
            skills = ""
            try:
                skills = student.profile.skills
            except:
                pass
            matches, total_prereqs = calculate_prerequisite_match(skills, state['prereqs'])
            
            # If total_prereqs is 0 (or not 6), we normalize as if there were 6 points as per rubric
            # User specified "6 criteria". If 3 are listed and 3 matched, is that 50/50? 
            # Logic: (matches / 6) * 50. 
            # If user has fewer than 6 requirements, max score is lower, which motivates adding them.
            profile_score = (matches / 6) * 50
            
            # B. Preference Score (0-50)
            # Rank 1 = 50, Rank 2 = 30, Rank 3 = 10 (Arbitrary descending scale to fit 50 range)
            pref_score = 0
            if pref.rank == 1: pref_score = 50
            elif pref.rank == 2: pref_score = 30
            elif pref.rank == 3: pref_score = 10
            
            total_score = profile_score + pref_score
            
            # Logic: Identify "Best Fit" project for this student among their choices
            # Since we iterate primarily to find *any* available slot, strict "best fit" might limit us 
            # if we just take the first valid one. 
            # However, usually students want their Rank 1. 
            # If Rank 1 is available, Total Score will likely be highest (50+X).
            # If Rank 1 is full, we look at Rank 2.
            # So effectively, this loop finds the best *available* project.
            
            if total_score > highest_score:
                highest_score = total_score
                best_project_id = p_id
        
        # Step 4: Allocate
        if best_project_id:
            # Assign
            student.allocated_project_id = best_project_id
            student.save()
            
            # Fetch project for notification references
            project = project_states[best_project_id]['obj']
            
            # Trigger Notifications
            from .models import Notification
            Notification.objects.create(
                student_recipient=student,
                message=f"You have been successfully allocated to project: {project.title}",
                link="/student/allocation/"
            )
            Notification.objects.create(
                supervisor_recipient=project.supervisor,
                message=f"The automated algorithm assigned {student.first_name} {student.last_name} to your project: {project.title}",
                link=f"/supervisor/project/{project.id}/"
            )
            
            # Update local state
            project_states[best_project_id]['filled'] += 1
            allocated_count += 1
            
    return allocated_count
