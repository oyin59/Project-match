from .models import Notification

def notifications(request):
    """
    Context processor to inject unread notifications globally.
    Checks session for user_id and user_role to fetch the correct notifications.
    """
    user_id = request.session.get("user_id")
    user_role = request.session.get("user_role")
    
    unread_notifications = []
    
    if user_id and user_role:
        if user_role == "student":
            unread_notifications = Notification.objects.filter(student_recipient_id=user_id, is_read=False)
        elif user_role == "supervisor":
            unread_notifications = Notification.objects.filter(supervisor_recipient_id=user_id, is_read=False)
        elif user_role == "admin":
            unread_notifications = Notification.objects.filter(admin_recipient_id=user_id, is_read=False)
            
    return {
        'unread_notifications': unread_notifications,
        'unread_notifications_count': len(unread_notifications) if unread_notifications else 0
    }
