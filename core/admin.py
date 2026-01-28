from django.contrib import admin
from .models import Student, Supervisor, Admin, Project, Department, Module, StudentProfileDetails, StudentModule, Course

# Register your models here.
admin.site.register(Student)
admin.site.register(Supervisor)
admin.site.register(Admin)
admin.site.register(Project)
admin.site.register(Department)
admin.site.register(Module)
admin.site.register(StudentProfileDetails)
admin.site.register(StudentModule)
admin.site.register(Course)