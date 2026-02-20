from core.models import Supervisor, Project, Student, StudentPreference
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
import random

# Setup
s = Supervisor.objects.first()
p = s.projects.first()

print(f"Supervisor: {s}")
print(f"Project: {p.title}, Quota: {p.quota}")

# Ensure we have enough students
while Student.objects.count() < 3:
    Student.objects.create(email=f"temp_stud_{random.randint(1000,9999)}@example.com", password="pass")

students = list(Student.objects.all()[:3]) # Get 3 students

# Clear state
StudentPreference.objects.all().delete()
Student.objects.all().update(allocated_project=None)

# Initial Check
initial_sum = Supervisor.objects.filter(id=s.id).annotate(
    total_quota=Coalesce(Sum('projects__quota'), 0)
).first().total_quota
print(f"Initial Total Quota: {initial_sum}")

# Add state causing potential Cartesian product
# 1. Allocate a student to the project (One join branch)
print("Allocating Student 1 to project...")
students[0].allocated_project = p
students[0].save()

# 2. Add preferences for other students (Other join branch)
print("Adding preference for Student 2...")
StudentPreference.objects.create(student=students[1], project=p, rank=1)
print("Adding preference for Student 3...")
StudentPreference.objects.create(student=students[2], project=p, rank=2)

# Check sum again with full annotation from views.py
qs = Supervisor.objects.filter(id=s.id).annotate(
    total_projects=Count('projects', distinct=True),
    total_quota=Coalesce(Sum('projects__quota'), 0),
    total_allocated=Count('projects__allocated_students', distinct=True),
    total_interested=Count('projects__studentpreference__student', distinct=True)
)

final_val = qs.first()
print(f"Final Total Quota: {final_val.total_quota}")
print(f"Allocated Count: {final_val.total_allocated}")
print(f"Interested Count: {final_val.total_interested}")

if final_val.total_quota > initial_sum:
    print(f"BUG REPRODUCED: Quota sum increased from {initial_sum} to {final_val.total_quota}!")
else:
    print("No bug found. Sum is stable.")
