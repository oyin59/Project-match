from django.db import models


class Admin(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=225)

    def __str__(self):
        return self.email


class Supervisor(models.Model):
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=225)

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="courses"
    )
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name}"

class Module(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules"
    )
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.name}"



class Project(models.Model):
    supervisor = models.ForeignKey(
        Supervisor,
        on_delete=models.CASCADE,
        related_name="projects"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    prerequisites = models.CharField(max_length=255, blank=True)
    quota = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.title


class Student(models.Model):
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=225)

    preferences_submitted = models.BooleanField(default=False)
    allocated_project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="allocated_students"
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class StudentProfileDetails(models.Model):
    PROFILE_STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
    ]

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    student_number = models.CharField(max_length=50, blank=True)


    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    academic_summary = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    research_interests = models.TextField(blank=True)

    profile_status = models.CharField(
        max_length=10,
        choices=PROFILE_STATUS_CHOICES,
        default="DRAFT"
    )

    def __str__(self):
        return f"Profile - {self.student.email}"


class StudentModule(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="student_modules"
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="module_students"
    )

    class Meta:
        unique_together = ("student", "module")

    def __str__(self):
        return f"{self.student.email} - {self.module.code}"


