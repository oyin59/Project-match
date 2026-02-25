from django.core.management.base import BaseCommand
from core.models import Student, Supervisor, Admin, Project, Department, Course, Module, StudentModule

class Command(BaseCommand):
    help = 'Seeds the database with the final dataset'

    def handle(self, *args, **kwargs):
        # 1. Clear existing data
        self.stdout.write("Clearing existing data...")
        Project.objects.all().delete()
        Student.objects.all().delete()
        Supervisor.objects.all().delete()
        Admin.objects.all().delete()
        Course.objects.all().delete()
        Department.objects.all().delete()
        Module.objects.all().delete()
        StudentModule.objects.all().delete()

        # 2. Add Department
        dept = Department.objects.create(name="Department of Engineering and Physical Sciences", code="EPS")
        self.stdout.write("Added Department: EPS")

        # 3. Add Course
        course = Course.objects.create(name="BSc Computer Science", department=dept)
        self.stdout.write("Added Course: Computer Science")

        # 3.5. Add Modules
        modules_data = [
            ("CS3CA", "Computer Animation"),
            ("CS3GD", "Game Development"),
            ("CS3ID", "Interaction Design"),
            ("CS3SPM", "Software Project Management"),
            ("DG3NLP", "Natural Language Processing"),
            ("CS2DSA", "Data Structures & Algorithms (Java)"),
            ("CS2HCI", "Human-Computer Interaction"),
            ("CS2AI", "Introduction to Artificial Intelligence"),
            ("CS2IS", "Information Security"),
            ("CS2PLC", "Programming Language Concepts"),
            ("CS2SE", "Software Engineering"),
            ("CS2TP", "Team Project"),
            ("CS3ECS", "Enterprise Computing Strategies"),
            ("CS3CI", "Computational Intelligence"),
            ("CS3MIR", "Multimedia Information Retrieval"),
            ("CS3IVP", "Image and Video Processing"),
            ("CS3DM", "Data Mining"),
            ("CS3MAS", "Multi Agent Systems"),
            ("CS3ADG", "Advanced Database Systems and GIS"),
            ("CS3SA", "System Administration"),
            ("CS3SMC", "System Management, Access & Control")
        ]
        
        unique_modules = {code: name for code, name in modules_data}
        for code, name in unique_modules.items():
            Module.objects.create(course=course, code=code, name=name)
        self.stdout.write(f"Added {len(unique_modules)} Modules")

        # 4. Add Admin
        Admin.objects.create(
            email="grace.adebayo@projectmatch.py",
            password="admin123"
        )
        self.stdout.write("Added Admin: Grace Adebayo")

        # 5. Add Supervisors
        supervisors_data = [
            ("Michael", "Johnson", "michael.johnson@projectmatch.py"),
            ("Fatima", "Bello", "fatima.bello@projectmatch.py"),
            ("Daniel", "Okonkwo", "daniel.okonkwo@projectmatch.py"),
            ("Sarah", "Williams", "sarah.williams@projectmatch.py"),
            ("James", "Patel", "james.patel@projectmatch.py"),
        ]
        
        supervisors = {}
        for fname, lname, email in supervisors_data:
            sup = Supervisor.objects.create(
                first_name=fname, 
                last_name=lname, 
                email=email,
                password="supervisor123",
                courses="BSc Computer Science"
            )
            supervisors[fname] = sup

        self.stdout.write(f"Added {len(supervisors)} Supervisors")

        # 6. Add Students
        students_data = [
            ("Oyinlola", "Akinwale", "oyinlola.akinwale@projectmatch.py"),
            ("David", "Mensah", "david.mensah@projectmatch.py"),
            ("Aisha", "Mohammed", "aisha.mohammed@projectmatch.py"),
            ("Chinedu", "Eze", "chinedu.eze@projectmatch.py"),
            ("Sarah", "Thompson", "sarah.thompson@projectmatch.py"),
            ("Daniel", "Kim", "daniel.kim@projectmatch.py"),
            ("Blessing", "Adeyemi", "blessing.adeyemi@projectmatch.py"),
            ("Joshua", "Brown", "joshua.brown@projectmatch.py"),
            ("Fatou", "Ndiaye", "fatou.ndiaye@projectmatch.py"),
            ("Ibrahim", "Hassan", "ibrahim.hassan@projectmatch.py"),
            ("Emily", "Clarke", "emily.clarke@projectmatch.py"),
            ("Tunde", "Bakare", "tunde.bakare@projectmatch.py"),
            ("Priya", "Sharma", "priya.sharma@projectmatch.py"),
            ("Ahmed", "Ali", "ahmed.ali@projectmatch.py"),
            ("Jessica", "White", "jessica.white@projectmatch.py"),
        ]

        for fname, lname, email in students_data:
            Student.objects.create(
                first_name=fname, 
                last_name=lname, 
                email=email,
                password="student123"
            )
            
        self.stdout.write(f"Added {len(students_data)} Students")

        # 7. Add Projects
        def create_project(title, desc, reqs, supervisor_fname):
            req_str = "\n".join([f"- {r}" for r in reqs])
            Project.objects.create(
                title=title,
                description=desc,
                prerequisites=req_str,
                quota=3,
                supervisor=supervisors[supervisor_fname]
            )

        # Michael Johnson
        create_project("AI-Based Student Performance Prediction",
                       "Develop a predictive analytics system that analyses historical academic data such as grades, attendance records, and coursework submissions to forecast student performance. The system should include machine learning models, data preprocessing pipelines, and a dashboard for visualising predictions and trends.",
                       ["Data Structures & Algorithms", "Introduction to Artificial Intelligence", "Python Programming", "Basic Statistics"],
                       "Michael")
        create_project("Smart Attendance System Using Facial Recognition",
                       "Design and implement an automated attendance system that captures real-time images, detects and recognises faces, and records attendance securely in a central database.",
                       ["Computer Vision Fundamentals", "Linear Algebra", "Python Programming", "Database Systems"],
                       "Michael")
        create_project("University Helpdesk Chatbot",
                       "Develop an AI-powered chatbot capable of responding to student queries regarding timetables, deadlines, and administrative processes using natural language processing techniques.",
                       ["Natural Language Processing Basics", "Software Engineering", "Python Programming", "REST API Development"],
                       "Michael")

        # Fatima Bello
        create_project("Blockchain Certificate Verification System",
                       "Create a blockchain-based platform for issuing and verifying academic certificates securely, preventing forgery and enabling instant third-party validation.",
                       ["Distributed Systems", "Cryptography Fundamentals", "Web Development", "Smart Contract Concepts"],
                       "Fatima")
        create_project("Digital Library Management System",
                       "Develop a digital library system that manages book inventories, borrowing records, overdue tracking, and reporting features within a secure web platform.",
                       ["Database Systems", "Software Engineering", "Django or Web Framework Experience", "SQL Query Design"],
                       "Fatima")
        create_project("Cybersecurity Threat Monitoring Dashboard",
                       "Build a dashboard that analyses network traffic logs, detects anomalies, and visualises potential cybersecurity threats in real time.",
                       ["Computer Networks", "Cybersecurity Principles", "Python Programming", "Data Visualisation"],
                       "Fatima")

        # Daniel Okonkwo
        create_project("Secure Online Voting Platform",
                       "Develop a secure online voting system with encrypted vote storage, authentication controls, and tamper-resistant vote counting mechanisms.",
                       ["Cryptography", "Authentication Systems", "Database Systems", "Web Application Security"],
                       "Daniel")
        create_project("Hospital Appointment Booking System",
                       "Design a scalable hospital appointment platform with role-based access, booking management, notifications, and scheduling conflict resolution.",
                       ["Software Engineering", "Database Systems", "REST API Development", "UI/UX Design Principles"],
                       "Daniel")
        create_project("AI Resume Screening Tool",
                       "Develop an intelligent system that extracts skills from resumes using NLP techniques and ranks candidates based on job descriptions through machine learning models.",
                       ["Machine Learning", "Natural Language Processing", "Python Programming", "Data Preprocessing Techniques"],
                       "Daniel")

        # Sarah Williams
        create_project("Smart Traffic Monitoring System",
                       "Create a system that analyses traffic sensor or video data to identify congestion patterns and predict peak traffic periods.",
                       ["Data Analytics", "Computer Vision Basics", "Python Programming", "Statistical Modelling"],
                       "Sarah")
        create_project("IoT Energy Consumption Tracker",
                       "Develop an IoT-enabled dashboard that collects real-time energy consumption data from sensors and presents interactive analytics visualisations.",
                       ["Internet of Things Fundamentals", "Embedded Systems Basics", "Python Programming", "Data Visualisation"],
                       "Sarah")
        create_project("Mobile Budget Tracking Application",
                       "Design and implement a responsive budgeting application that allows users to track income, expenses, savings goals, and generate financial summaries.",
                       ["Web Development", "Database Systems", "JavaScript Fundamentals", "Software Design Patterns"],
                       "Sarah")

        # James Patel
        create_project("Cloud File Sharing Platform",
                       "Build a secure cloud-based file storage and sharing system featuring authentication, role-based permissions, encrypted file storage, and activity tracking.",
                       ["Cloud Computing Basics", "Web Security", "Database Systems", "Backend Development"],
                       "James")
        create_project("E-Commerce Recommendation Engine",
                       "Develop a recommendation engine that suggests products based on user behaviour, ratings, and transaction history using collaborative and content-based filtering techniques.",
                       ["Machine Learning", "Data Mining", "Python Programming", "Linear Algebra"],
                       "James")
        create_project("Student Internship Matching System",
                       "Create a matching system that pairs students with internship opportunities based on skills, interests, and employer requirements using ranking algorithms.",
                       ["Algorithms & Complexity", "Database Systems", "Backend Development", "Data Filtering Techniques"],
                       "James")
        
        self.stdout.write("Added 15 Projects")
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
