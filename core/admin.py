from django.contrib import admin
from .models import Student, Supervisor, Admin, Project

# Register your models here.
admin.site.register(Student)
admin.site.register(Supervisor)
admin.site.register(Admin)
admin.site.register(Project)