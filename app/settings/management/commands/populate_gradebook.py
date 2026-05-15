from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app.settings.models import Student, Lesson, StudentGrade, Cursues, Mentor, Enrollment

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with demo data for gradebook'

    def handle(self, *args, **options):
        self.stdout.write('Populating gradebook with demo data...')
        
        # Получаем или создаем ментора
        mentor_user, created = User.objects.get_or_create(
            username='demo_mentor',
            defaults={
                'first_name': 'Demo',
                'last_name': 'Mentor',
                'role': 'Ментор',
                'phone_number': '+996700000000'
            }
        )
        
        mentor, created = Mentor.objects.get_or_create(
            user=mentor_user,
            defaults={
                'middle_name': 'Ivanovich',
                'skills': 'Python, JavaScript, Django',
                'workplace': 'Geeks Academy'
            }
        )
        
        # Получаем или создаем курс
        course, created = Cursues.objects.get_or_create(
            title='JavaScript Advanced',
            defaults={
                'description': 'Advanced JavaScript course',
                'price': 15000,
                'duration': '3 months'
            }
        )
        course.mentors.add(mentor)
        
        # Создаем 7 студентов
        student_names = [
            'Алиев Бакыт',
            'Бакирова Айгуль', 
            'Джумабаев Эрмек',
            'Каримова Динара',
            'Мамытов Нурбек',
            'Нурматова Айдана',
            'Турсунов Азамат'
        ]
        
        students = []
        for i, name in enumerate(student_names):
            last_name, first_name = name.split(' ', 1)
            user, created = User.objects.get_or_create(
                username=f'student_{i+1}',
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'Студент',
                    'phone_number': f'+99670000000{i+1}'
                }
            )
            
            student, created = Student.objects.get_or_create(
                user=user,
                defaults={
                    'birth_date': '2005-01-01'
                }
            )
            students.append(student)
            
            # Создаем enrollment
            Enrollment.objects.get_or_create(
                student=student,
                course=course
            )
        
        # Создаем 15 уроков
        lessons = []
        for i in range(1, 16):
            lesson, created = Lesson.objects.get_or_create(
                course=course,
                order=i,
                defaults={
                    'title': f'Урок {i}',
                    'description': f'Описание урока {i}',
                    'mentor': mentor
                }
            )
            lessons.append(lesson)
        
        # Создаем оценки для каждого студента и урока
        import random
        for student in students:
            for lesson in lessons:
                # Случайная оценка 0 или 1
                grade_value = random.choice([0, 1])
                
                StudentGrade.objects.get_or_create(
                    student=student,
                    lesson=lesson,
                    defaults={
                        'grade': grade_value,
                        'comment': f'Комментарий для студента {student.user.last_name} на уроке {lesson.order}'
                    }
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully populated gradebook with demo data!'))
        self.stdout.write(f'Created {len(students)} students')
        self.stdout.write(f'Created {len(lessons)} lessons')
        self.stdout.write(f'Created {len(students) * len(lessons)} grades')
