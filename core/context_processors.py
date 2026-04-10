from .models import Notification, Student, Supervisor, Admin

def notifications(request):
    """
    Context processor to inject unread notifications globally.
    Checks session for user_id and user_role to fetch the correct notifications.
    """
    user_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    
    unread_notifications = []
    user_initials = request.session.get("user_email", "U")[0].upper()
    
    if user_id and user_role:
        if user_role == "student":
            unread_notifications = Notification.objects.filter(student_recipient_id=user_id, is_read=False)
            student = Student.objects.filter(id=user_id).first()
            if student and student.first_name:
                user_initials = student.first_name[0].upper()
        elif user_role == "supervisor":
            unread_notifications = Notification.objects.filter(supervisor_recipient_id=user_id, is_read=False)
            supervisor = Supervisor.objects.filter(id=user_id).first()
            if supervisor and supervisor.first_name:
                user_initials = supervisor.first_name[0].upper()
        elif user_role == "admin":
            unread_notifications = Notification.objects.filter(admin_recipient_id=user_id, is_read=False)
            user_initials = "A"
            
    return {
        'unread_notifications': unread_notifications,
        'unread_notifications_count': len(unread_notifications) if unread_notifications else 0,
        'user_initials': user_initials
    }
