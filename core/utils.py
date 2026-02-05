def calculate_prerequisite_match(student_skills: str, project_prerequisites: str) -> tuple[int, int]:
    """
    Compare student skills against project prerequisites.
    Returns (matched_count, total_count).
    Case-insensitive. Handles comma-separated strings.
    """
    if not project_prerequisites:
        return 0, 0

    # Parse and normalize prerequisites
    prereqs = [p.strip().lower() for p in project_prerequisites.split(',') if p.strip()]
    if not prereqs:
        return 0, 0

    if not student_skills:
        return 0, len(prereqs)

    # Parse and normalize skills
    skills = set(s.strip().lower() for s in student_skills.split(',') if s.strip())

    # Count matches
    matched_count = sum(1 for p in prereqs if p in skills)
    
    return matched_count, len(prereqs)
