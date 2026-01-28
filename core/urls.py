# app_name/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # Student
    path("student/", views.student_dashboard, name="student_dashboard"),
    path("student/profile/", views.student_profile, name="student_profile"),
    path("student/projects/", views.student_projects, name="student_projects"),
    path("student/projects/<int:project_id>/", views.student_project_detail, name="student_project_detail"),
    path("student/preferences/", views.student_preferences, name="student_preferences"),

    # AJAX
    path("ajax/load-modules/", views.ajax_load_modules, name="ajax_load_modules"),
    path("ajax/load-courses/", views.ajax_load_courses, name="ajax_load_courses"),

    # Supervisor
    path("supervisor/", views.supervisor_dashboard, name="supervisor_dashboard"),
    path("supervisor/projects/", views.supervisor_projects, name="supervisor_projects"),
    path("supervisor/add-projects/", views.supervisor_add_project, name="supervisor_add_project"),
    path('supervisor/project/<int:project_id>/edit/', views.supervisor_edit_project, name='supervisor_edit_project'),
    path('supervisor/project/<int:project_id>/', views.supervisor_project_detail, name='supervisor_project_detail'),
    path("supervisor/interested-students/", views.supervisor_interested_students, name="supervisor_interested_students"),

    # Admin
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-students/", views.admin_students, name="admin_students"),
    path("admin-projects/", views.admin_projects, name="admin_projects"),
    path("admin-supervisors/", views.admin_supervisors, name="admin_supervisors"),
    path("admin-allocations/", views.admin_allocations, name="admin_allocations"),
    path("admin-manual-allocations/", views.admin_manual_allocations, name="admin_manual_allocations"),
]
