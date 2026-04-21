from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.hashers import make_password, check_password as django_check_password



class Admin(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=225)

    def __str__(self):
        return self.email

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)


class Supervisor(models.Model):
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=225)
    courses = models.TextField(default="Computer Science", blank=True, help_text="Comma-separated list of courses (e.g., 'Computer Science, Software Engineering')")

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)


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
    quota = models.IntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(50)
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.title


class Student(models.Model):
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=225)

    preferences_submitted = models.BooleanField(default=False)
    preferences_submitted_at = models.DateTimeField(null=True, blank=True)
    allocated_project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="allocated_students"
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)


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

    student_number = models.CharField(
        max_length=15, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{8,12}$',
                message="Student ID must be numeric and between 8 to 12 digits."
            )
        ]
    )


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


class StudentPreference(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="preferences"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    rank = models.IntegerField(default=0)  # 0 = Unranked, 1, 2, 3 = Ranked

    class Meta:
        unique_together = ("student", "project")
        ordering = ["rank"]

    def __str__(self):
        return f"{self.student.email} - {self.project.title} (Rank {self.rank})"


class Notification(models.Model):
    # Recipient can be any of the three user types
    student_recipient = models.ForeignKey(Student, null=True, blank=True, on_delete=models.CASCADE, related_name="notifications")
    supervisor_recipient = models.ForeignKey(Supervisor, null=True, blank=True, on_delete=models.CASCADE, related_name="notifications")
    admin_recipient = models.ForeignKey(Admin, null=True, blank=True, on_delete=models.CASCADE, related_name="notifications")
    
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, help_text="Optional URL to redirect to when clicked")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification: {self.message}"


class AuditLog(models.Model):
    LOG_LEVEL_CHOICES = [
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    user_description = models.CharField(max_length=255, help_text="e.g. Student (ID 210...), Admin, etc.")
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    log_level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES, default="INFO")

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.user_description}: {self.action}"
