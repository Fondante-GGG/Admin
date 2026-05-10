from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class ManagerAccessMiddleware(MiddlewareMixin):

    
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
            
        if hasattr(request.user, 'role') and request.user.role == 'Менеджер':
            jazzmin_settings = getattr(settings, 'JAZZMIN_SETTINGS', {})
            
            jazzmin_settings['hide_models'] = [
                'settings.accountingentry',
                'settings.accountingaccount', 
                'settings.accountingproject',
                'settings.accountingcategory',
                'settings.salary',
            ]
            
            # Убеждаемся что основные разделы видны
            if 'settings' not in jazzmin_settings.get('order_with_respect_to', []):
                jazzmin_settings.setdefault('order_with_respect_to', []).extend([
                    'settings',
                    'settings.cursues',
                    'settings.groupcourse', 
                    'settings.individualcourse',
                    'settings.student',
                    'settings.mentor',
                    'settings.lead',
                    'settings.call',
                    'settings.task',
                    'settings.calendarevent',
                    'config',
                ])
                
        return None
