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


def run_allocation_algorithm(weight_pref=50, weight_qual=50):
    """
    Executes the automated allocation process based on user-defined logic:
    1. Filter eligible students (Profile & Prefs submitted, Unallocated).
    2. Sort by student ID to maintain consistency.
    3. For each student, calculate scores for their preferred projects using Dynamic Weighting:
       - Qualification Score (Dominant): (Matches / TotalPrereqs) * weight_qual
       - Preference Bonus (Nudge): Scaled bonus based on rank and weight_pref
       - Total Score = QualScore + (PrefBonus * weight_pref / 100)
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
    # Remove speed bias (earliest first) as a primary metric for fairness.
    # We now order non-deterministically (or by student ID) so login speed doesn't guarantee Rank 1.
    sorted_students = eligible_students.order_by('id')
    
    # Track project capacities in memory to avoid DB hits in loop
    projects = Project.objects.annotate(current_allocations=Count('allocated_students'))
    project_states = {p.id: {'obj': p, 'filled': p.current_allocations, 'quota': p.quota, 'prereqs': p.prerequisites} for p in projects}
    
    allocated_count = 0
    
    for student in sorted_students:
        best_project_id = None
        highest_score = -1
        
        # Get Student's Preferences (Strictly ignore unranked/rank=0)
        preferences = StudentPreference.objects.filter(student=student, rank__gt=0).order_by('rank')
        
        for pref in preferences:
            p_id = pref.project.id
            if p_id not in project_states:
                continue
                
            state = project_states[p_id]
            
            # Check Quota
            if state['filled'] >= state['quota']:
                continue
                
            # Step 3: Compute Scores (Option 3 - Qualification Dominant)
            
            # A. Qualification Score (0 to weight_qual)
            skills = ""
            try:
                skills = student.profile.skills
            except:
                pass
            
            matches, total_prereqs = calculate_prerequisite_match(skills, state['prereqs'])
            
            if total_prereqs > 0:
                qual_score = (matches / total_prereqs) * float(weight_qual)
            else:
                # If project has no prerequisites, it's accessible to all with base score
                qual_score = float(weight_qual) * 0.5 
            
            # B. Preference Bonus (Nudge)
            # We use a base bonus (10, 5, 2) and scale it by the weight_pref
            # This ensures preference "nudges" the outcome but rarely overpowers a large skill gap.
            rank_bonus_base = 0
            if pref.rank == 1: rank_bonus_base = 10
            elif pref.rank == 2: rank_bonus_base = 5
            elif pref.rank == 3: rank_bonus_base = 2
            
            pref_bonus = rank_bonus_base * (float(weight_pref) / 100.0)
            
            total_score = qual_score + pref_bonus
            
            # Log the scoring for transparency (can be seen in server logs)
            print(f"DEBUG: Student {student.email} -> Project {p_id}: Qual={qual_score:.2f}, PrefBonus={pref_bonus:.2f}, Total={total_score:.2f}")

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
