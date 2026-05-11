from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time
from app.settings.models import Mentor, TimeSlot, Schedule, Cursues

class Command(BaseCommand):
    help = 'Create test schedule data for mentors'

    def handle(self, *args, **options):
        self.stdout.write('Creating schedule data...')
        
        # Находим ментора beksultan-beksultan
        try:
            user = Mentor.objects.get(user__username='beksultan-beksultan')
        except Mentor.DoesNotExist:
            self.stdout.write('ERROR: Mentor beksultan-beksultan not found')
            return
        
        # Создаем временные слоты
        time_slots_data = [
            # Понедельник
            {'day': 'monday', 'start': time(9, 0), 'end': time(10, 30)},
            {'day': 'monday', 'start': time(11, 0), 'end': time(12, 30)},
            {'day': 'monday', 'start': time(14, 0), 'end': time(15, 30)},
            {'day': 'monday', 'start': time(16, 0), 'end': time(17, 30)},
            
            # Вторник
            {'day': 'tuesday', 'start': time(9, 0), 'end': time(10, 30)},
            {'day': 'tuesday', 'start': time(11, 0), 'end': time(12, 30)},
            {'day': 'tuesday', 'start': time(14, 0), 'end': time(15, 30)},
            {'day': 'tuesday', 'start': time(16, 0), 'end': time(17, 30)},
            
            # Среда
            {'day': 'wednesday', 'start': time(9, 0), 'end': time(10, 30)},
            {'day': 'wednesday', 'start': time(11, 0), 'end': time(12, 30)},
            {'day': 'wednesday', 'start': time(14, 0), 'end': time(15, 30)},
            {'day': 'wednesday', 'start': time(16, 0), 'end': time(17, 30)},
            
            # Четверг
            {'day': 'thursday', 'start': time(9, 0), 'end': time(10, 30)},
            {'day': 'thursday', 'start': time(11, 0), 'end': time(12, 30)},
            {'day': 'thursday', 'start': time(14, 0), 'end': time(15, 30)},
            {'day': 'thursday', 'start': time(16, 0), 'end': time(17, 30)},
            
            # Пятница
            {'day': 'friday', 'start': time(9, 0), 'end': time(10, 30)},
            {'day': 'friday', 'start': time(11, 0), 'end': time(12, 30)},
            {'day': 'friday', 'start': time(14, 0), 'end': time(15, 30)},
            {'day': 'friday', 'start': time(16, 0), 'end': time(17, 30)},
            
            # Суббота
            {'day': 'saturday', 'start': time(10, 0), 'end': time(11, 30)},
            {'day': 'saturday', 'start': time(12, 0), 'end': time(13, 30)},
        ]
        
        created_time_slots = 0
        for slot_data in time_slots_data:
            time_slot, created = TimeSlot.objects.get_or_create(
                day_of_week=slot_data['day'],
                start_time=slot_data['start'],
                end_time=slot_data['end'],
                defaults={'is_active': True}
            )
            if created:
                created_time_slots += 1
                self.stdout.write(f'  Created time slot: {time_slot}')
        
        # Получаем курсы ментора
        courses = Cursues.objects.filter(mentors=user)
        
        if not courses.exists():
            self.stdout.write('ERROR: No courses found for mentor')
            return
        
        # Создаем расписание для некоторых курсов
        schedule_data = [
            # Понедельник - Python Start
            {'day': 'monday', 'start': time(9, 0), 'course': 'Python Start', 'room': '201'},
            {'day': 'monday', 'start': time(11, 0), 'course': 'Python Start', 'room': '201'},
            
            # Вторник - Web Development Basic
            {'day': 'tuesday', 'start': time(14, 0), 'course': 'Web Development Basic', 'room': '305'},
            {'day': 'tuesday', 'start': time(16, 0), 'course': 'Web Development Basic', 'room': '305'},
            
            # Среда - JavaScript Advanced
            {'day': 'wednesday', 'start': time(9, 0), 'course': 'JavaScript Advanced', 'room': '402'},
            {'day': 'wednesday', 'start': time(11, 0), 'course': 'JavaScript Advanced', 'room': '402'},
            
            # Четверг - Python Individual 1
            {'day': 'thursday', 'start': time(14, 0), 'course': 'Python Individual 1', 'room': '103'},
            
            # Пятница - JavaScript Individual 1
            {'day': 'friday', 'start': time(16, 0), 'course': 'JavaScript Individual 1', 'room': '104'},
            
            # Суббота - Web Design Individual
            {'day': 'saturday', 'start': time(10, 0), 'course': 'Web Design Individual', 'room': '205'},
        ]
        
        created_schedules = 0
        for sched_data in schedule_data:
            # Находим курс
            try:
                course = courses.get(title=sched_data['course'])
            except Cursues.DoesNotExist:
                continue
            
            # Находим временной слот
            try:
                time_slot = TimeSlot.objects.get(
                    day_of_week=sched_data['day'],
                    start_time=sched_data['start']
                )
            except TimeSlot.DoesNotExist:
                continue
            
            # Создаем расписание
            schedule, created = Schedule.objects.get_or_create(
                mentor=user,
                course=course,
                time_slot=time_slot,
                defaults={'room': sched_data['room'], 'is_active': True}
            )
            
            if created:
                created_schedules += 1
                self.stdout.write(f'  Created schedule: {schedule}')
        
        self.stdout.write(f'\n✅ Created {created_time_slots} time slots and {created_schedules} schedules')
        self.stdout.write('Schedule data is ready!')
