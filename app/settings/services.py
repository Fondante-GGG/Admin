from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

class NotificationService:
    @staticmethod
    def create_notification(recipient, sender, title, message, notification_type='system', related_lesson=None):
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            type=notification_type,
            title=title,
            message=message,
            related_lesson=related_lesson
        )

        channel_layer = get_channel_layer()
        user_group_name = f"user_{recipient.id}"
        
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'related_lesson': {
                'id': notification.related_lesson.id,
                'title': notification.related_lesson.title
            } if notification.related_lesson else None
        }
        
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'notification_message',
                'notification': notification_data
            }
        )
        
        return notification
    
    @staticmethod
    def create_homework_notification(student, lesson, homework_title):
        # Homework submissions are disabled in the mentor portal.
        return None
