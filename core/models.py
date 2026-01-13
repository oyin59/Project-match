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
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.email
    

class Project(models.Model):
    """
    Projects offered by supervisors.
    This is what students will see on the Projects page.
    """
    supervisor = models.ForeignKey(
        Supervisor, 
        on_delete=models.CASCADE,
        related_name="projects",
    )

    title = models.CharField(max_length=255)
    description = models.TextField()

    prerequisites = models.CharField(
        max_length=255,
        blank=True,
        help_text="AI, Python, NLP"
    )

    quota = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at =models.DateTimeField(auto_now=True)

    def spaces_available(self):
        allocated = self.allocated_students.count()
        return max(self.quota - allocated , 0)
    
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
        related_name="allocated_students",
    )

    def __str__(self):
        if self.first_name or self.last_name:   
            return f"{self.first_name} {self.last_name}".strip()
        return self.email
    

