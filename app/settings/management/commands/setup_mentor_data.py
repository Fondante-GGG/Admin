from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from app.settings.models import User, Mentor, Student, Cursues, GroupCourse, IndividualCourse, Organization


class Command(BaseCommand):
    help = 'Setup test data for mentor beksultan-beksultan with courses and students'

    def handle(self, *args, **options):
        try:
            # Найти пользователя beksultan-beksultan
            user = User.objects.get(username='beksultan-beksultan')
            self.stdout.write(f'Found user: {user.username}, role: {user.role}')
            
            mentor, created = Mentor.objects.get_or_create(user=user)
            if created:
                self.stdout.write(f'Created mentor profile for {user.username}')
            else:
                self.stdout.write(f'Mentor profile already exists for {user.username}')
            
            org, _ = Organization.objects.get_or_create(
                name='Test Organization',
                defaults={'slug': 'test-org'}
            )
            mentor.organization = org
            mentor.save()
            
            students_data = [
                {'first_name': 'Асылбек', 'last_name': 'Нурдаулет'},
                {'first_name': 'Данияр', 'last_name': 'Абдулла'},
                {'first_name': 'Айгерим', 'last_name': 'Толеу'},
                {'first_name': 'Мади', 'last_name': 'Жумабек'},
                {'first_name': 'Аружан', 'last_name': 'Серик'},
                {'first_name': 'Нурислам', 'last_name': 'Беков'},
                {'first_name': 'Дина', 'last_name': 'Алиева'},
                {'first_name': 'Тимур', 'last_name': 'Кадыров'},
                {'first_name': 'Айсулу', 'last_name': 'Махамбет'},
                {'first_name': 'Ербол', 'last_name': 'Нурманов'},
                {'first_name': 'Самат', 'last_name': 'Байгозин'},
                {'first_name': 'Гульназ', 'last_name': 'Смаилова'},
            ]
            
            students = []
            for i, student_data in enumerate(students_data, 1):
                username = f"student{i}_{timezone.now().strftime('%Y%m%d')}"
                student_user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': student_data['first_name'],
                        'last_name': student_data['last_name'],
                        'role': 'Студент',
                        'is_active': True,
                    }
                )
                student, created = Student.objects.get_or_create(
                    user=student_user,
                    defaults={
                        'birth_date': date(2000 + (i % 5), 1 + (i % 11), 1 + (i % 25)),
                        'parent_phone': f'+996700{i:03d}',
                    }
                )
                students.append(student)
                if created:
                    self.stdout.write(f'Created student: {student_data["first_name"]} {student_data["last_name"]}')
            
            # Создать групповые курсы
            group_courses_data = [
                {
                    'title': 'Python Start',
                    'subject': 'Python',
                    'capacity': 10,
                    'start': date.today(),
                    'end': date.today() + timedelta(days=90),
                    'students_count': 8,
                },
                {
                    'title': 'Web Development Basic',
                    'subject': 'HTML/CSS/JS',
                    'capacity': 12,
                    'start': date.today() - timedelta(days=30),
                    'end': date.today() + timedelta(days=60),
                    'students_count': 10,
                },
                {
                    'title': 'JavaScript Advanced',
                    'subject': 'JavaScript',
                    'capacity': 8,
                    'start': date.today(),
                    'end': date.today() + timedelta(days=60),
                    'students_count': 6,
                },
            ]
            
            group_courses = []
            for course_data in group_courses_data:
                course, created = GroupCourse.objects.get_or_create(
                    title=course_data['title'],
                    defaults={
                        'organization': org,
                        'subject': course_data['subject'],
                        'capacity': course_data['capacity'],
                        'start': course_data['start'],
                        'end': course_data['end'],
                        'status': 'active',
                        'price': 15000,
                        'lessons_per_month': 15,
                        'duration_days': (course_data['end'] - course_data['start']).days,
                    }
                )
                course.mentors.add(mentor)
                
                # Добавить студентов к курсу
                course_students = students[:course_data['students_count']]
                course.students.add(*course_students)
                
                group_courses.append(course)
                if created:
                    self.stdout.write(f'Created group course: {course.title} with {course_data["students_count"]} students')
                else:
                    self.stdout.write(f'Group course already exists: {course.title}')
            
            # Создать индивидуальные курсы
            individual_courses_data = [
                {
                    'title': 'Python Individual 1',
                    'subject': 'Python',
                    'start': date.today(),
                    'end': date.today() + timedelta(days=45),
                    'student_index': 8,
                },
                {
                    'title': 'JavaScript Individual 1',
                    'subject': 'JavaScript',
                    'start': date.today() - timedelta(days=15),
                    'end': date.today() + timedelta(days=30),
                    'student_index': 9,
                },
                {
                    'title': 'Web Design Individual',
                    'subject': 'Web Design',
                    'start': date.today(),
                    'end': date.today() + timedelta(days=60),
                    'student_index': 10,
                },
            ]
            
            individual_courses = []
            for course_data in individual_courses_data:
                course, created = IndividualCourse.objects.get_or_create(
                    title=course_data['title'],
                    defaults={
                        'organization': org,
                        'subject': course_data['subject'],
                        'capacity': 1,
                        'start': course_data['start'],
                        'end': course_data['end'],
                        'status': 'active',
                        'price': 25000,
                        'lessons_per_month': 8,
                        'duration_days': (course_data['end'] - course_data['start']).days,
                    }
                )
                course.mentors.add(mentor)
                
                # Добавить одного студента
                student = students[course_data['student_index']]
                course.students.add(student)
                
                individual_courses.append(course)
                if created:
                    self.stdout.write(f'Created individual course: {course.title} for {student.user.first_name} {student.user.last_name}')
                else:
                    self.stdout.write(f'Individual course already exists: {course.title}')
            
            # Вывод статистики
            self.stdout.write('\n=== СТАТИСТИКА ===')
            self.stdout.write(f'Ментор: {user.username}')
            self.stdout.write(f'Групповые курсы: {len(group_courses)}')
            self.stdout.write(f'Индивидуальные курсы: {len(individual_courses)}')
            self.stdout.write(f'Всего студентов создано: {len(students)}')
            
            self.stdout.write('\n=== ГРУППОВЫЕ КУРСЫ ===')
            for course in group_courses:
                self.stdout.write(f'{course.title}: {course.students.count()}/{course.capacity} студентов')
            
            self.stdout.write('\n=== ИНДИВИДУАЛЬНЫЕ КУРСЫ ===')
            for course in individual_courses:
                student_name = course.students.first().user.get_full_name() if course.students.exists() else 'Нет студента'
                self.stdout.write(f'{course.title}: {student_name}')
            
            self.stdout.write('\n✅ Данные успешно созданы!')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Пользователь beksultan-beksultan не найден'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
            import traceback
            traceback.print_exc()
