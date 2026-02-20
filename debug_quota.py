from core.models import Supervisor
from django.db.models import Sum

print("\n--- SUPERVISOR QUOTA DEBUG ---")
for s in Supervisor.objects.all():
    projects = s.projects.all()
    total = s.projects.aggregate(Sum('quota'))['quota__sum'] or 0
    breakdown = [f"{p.title}: {p.quota}" for p in projects]
    print(f"Supervisor: {s}")
    print(f"  Total Quota: {total}")
    print(f"  Project Count: {projects.count()}")
    print(f"  Breakdown: {breakdown}")
    print("-" * 30)
