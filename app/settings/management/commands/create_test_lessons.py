from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app.settings.models import User, Mentor, Cursues, Lesson

class Command(BaseCommand):
    help = 'Create test lessons for mentor courses'

    def handle(self, *args, **options):
        self.stdout.write('Creating test lessons...')
        
        # Находим ментора beksultan-beksultan
        try:
            user = User.objects.get(username='beksultan-beksultan')
            mentor = Mentor.objects.get(user=user)
        except (User.DoesNotExist, Mentor.DoesNotExist):
            self.stdout.write('ERROR: Mentor beksultan-beksultan not found')
            return
        
        # Получаем все курсы ментора
        courses = Cursues.objects.filter(mentors=mentor)
        
        if not courses.exists():
            self.stdout.write('ERROR: No courses found for mentor')
            return
        
        lesson_count = 0
        for course in courses:
            self.stdout.write(f'Creating lessons for course: {course.title}')
            
            # Создаем 15 уроков для каждого курса
            for i in range(1, 16):
                lesson, created = Lesson.objects.get_or_create(
                    mentor=mentor,
                    course=course,
                    order=i,
                    defaults={
                        'title': f'Урок №{i}',
                        'description': f'Описание урока №{i} для курса {course.title}',
                        'is_additional': i > 5,
                        'date': timezone.now().date() + timedelta(days=i-1),
                        'deadline': timezone.now() + timedelta(days=i+3),
                    }
                )
                
                if created:
                    lesson_count += 1
                    self.stdout.write(f'  Created: {lesson.title}')
                else:
                    self.stdout.write(f'  Exists: {lesson.title}')
        
        self.stdout.write(f'\n✅ Created {lesson_count} new lessons')
        self.stdout.write('Test lessons are ready!')
