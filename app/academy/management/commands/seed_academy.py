from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from app.academy.models import (
    AboutObjects,
    AboutObjects2,
    AboutPage,
    AboutStudents,
    Achievement,
    Address,
    Contacts,
    CourseApplication,
    Courses,
    CoursesModel,
    CoursesPage,
    CoursesProgram,
    Feedback,
    Settings,
    Students,
    Teacher,
    TypeCourse,
)


class Command(BaseCommand):
    help = "Заполняет модели academy осмысленными демо-данными."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить существующие данные academy перед заполнением.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()

        settings_obj = self._create_settings()
        contacts = self._create_contacts()
        self._create_about_page()
        self._create_about_blocks()
        directions = self._create_course_types()
        courses = self._create_courses(directions)
        self._create_course_page()
        self._create_teachers()
        self._create_students_page()
        self._create_student_stories()
        self._create_applications(courses)
        self._create_feedback()

        self.stdout.write(
            self.style.SUCCESS(
                f"Academy data seeded: settings={settings_obj.pk}, contacts={contacts.pk}, courses={len(courses)}"
            )
        )

    def _asset(self, relative_path: str) -> File:
        asset_path = Path(settings.BASE_DIR) / "static" / relative_path
        return File(asset_path.open("rb"), name=asset_path.name)

    def _create_settings(self) -> Settings:
        obj, _ = Settings.objects.update_or_create(
            pk=1,
            defaults={
                "title_banner": "American Dream Academy",
                "description_banner": (
                    "<p>Подготовка к IELTS, SAT и поступлению в зарубежные университеты "
                    "с понятной программой, сильными преподавателями и реальными результатами.</p>"
                ),
                "title_about": "Почему выбирают нас",
                "description_about": (
                    "<p>Мы выстраиваем обучение вокруг целей ученика: поступление, экзамены, "
                    "академический английский и уверенная разговорная практика.</p>"
                ),
                "title_about2": "Обучение с результатом",
                "description_about2": (
                    "<p>Каждый курс включает диагностику уровня, индивидуальный план и регулярную "
                    "обратную связь для родителей и студентов.</p>"
                ),
                "description_about3": (
                    "<p>Студенты учатся по международным материалам, тренируют speaking, writing "
                    "и готовятся к реальным форматам экзаменов.</p>"
                ),
                "description_about4": (
                    "<p>Наша цель не просто дать знания, а довести ученика до конкретного результата: "
                    "высокого балла, гранта или поступления.</p>"
                ),
                "popular_courses": "Популярные курсы",
                "our_teachers": "Наши преподаватели",
                "feedback": "Свяжитесь с нами",
                "feedback_description": (
                    "<p>Оставьте заявку, и мы подберем программу, которая подойдет по цели, "
                    "уровню английского и расписанию.</p>"
                ),
                "linksinsta": "https://instagram.com/americandream.academy",
                "linksyoutube": "https://youtube.com/@americandreamacademy",
                "linkstiktok": "https://tiktok.com/@americandreamacademy",
            },
        )
        obj.image_about.save("about-main.png", self._asset("img/people.png"), save=True)
        return obj

    def _create_contacts(self) -> Contacts:
        obj, _ = Contacts.objects.update_or_create(
            pk=1,
            defaults={
                "phone_numbers": "<p>+996 700 123 456<br>+996 555 987 654</p>",
                "email": "hello@americandream.kg",
                "address": "г. Бишкек, ул. Исанова 42/1",
                "links_email": "mailto:hello@americandream.kg",
                "links_address": "https://maps.google.com/?q=%D0%98%D1%81%D0%B0%D0%BD%D0%BE%D0%B2%D0%B0+42%2F1+%D0%91%D0%B8%D1%88%D0%BA%D0%B5%D0%BA",
            },
        )
        addresses = [
            ("Главный офис: г. Бишкек, ул. Исанова 42/1", "https://maps.google.com/?q=%D0%98%D1%81%D0%B0%D0%BD%D0%BE%D0%B2%D0%B0+42%2F1+%D0%91%D0%B8%D1%88%D0%BA%D0%B5%D0%BA"),
            ("Филиал: г. Бишкек, пр. Чуй 109", "https://maps.google.com/?q=%D0%A7%D1%83%D0%B9+109+%D0%91%D0%B8%D1%88%D0%BA%D0%B5%D0%BA"),
        ]
        obj.addresses.all().delete()
        for address, link in addresses:
            Address.objects.create(contact=obj, address=address, link=link)
        return obj

    def _create_about_page(self) -> None:
        AboutPage.objects.update_or_create(
            pk=1,
            defaults={
                "title_banner": "О нашей академии",
                "description_banner": (
                    "<p>American Dream Academy помогает школьникам и студентам выйти на "
                    "международный уровень подготовки и уверенно поступать в сильные вузы.</p>"
                ),
                "title": "Обучение, которое ведет к цели",
                "description": (
                    "<p>Мы объединили языковую подготовку, академическое сопровождение и работу "
                    "с мотивацией ученика. Поэтому наши программы подходят тем, кто хочет не просто "
                    "посещать занятия, а двигаться к конкретному результату.</p>"
                ),
            },
        )

    def _create_about_blocks(self) -> None:
        AboutObjects.objects.all().delete()
        blocks_one = [
            (
                "Подготовка к международным экзаменам",
                "<p>IELTS, SAT и Duolingo English Test с фокусом на структуру экзамена и рост балла.</p>",
                "img/aboutUs/IELTS.png",
            ),
            (
                "Поступление за рубеж",
                "<p>Помогаем собрать сильный профиль, подготовить эссе и пройти путь до зачисления.</p>",
                "img/aboutUs/BECB1HIGHTER.png",
            ),
            (
                "Академический английский",
                "<p>Развиваем writing, reading и speaking для учебы, интервью и международной среды.</p>",
                "img/aboutUs/SAT.png",
            ),
        ]
        for title, description, image_path in blocks_one:
            obj = AboutObjects(title=title, description=description)
            obj.image.save(Path(image_path).name, self._asset(image_path), save=False)
            obj.save()

        AboutObjects2.objects.all().delete()
        blocks_two = [
            (
                "Малые группы",
                "<p>В группах до 8 человек преподаватель успевает работать с каждым учеником адресно.</p>",
                "img/aboutUs/right/rec1.png",
            ),
            (
                "Прозрачный трекинг прогресса",
                "<p>Регулярные отчеты показывают, как растут навыки и где нужно усиление.</p>",
                "img/aboutUs/right/rec2.png",
            ),
        ]
        for title, description, image_path in blocks_two:
            obj = AboutObjects2(title=title, description=description)
            obj.image.save(Path(image_path).name, self._asset(image_path), save=False)
            obj.save()

    def _create_course_types(self) -> dict[str, TypeCourse]:
        titles = ["IELTS", "SAT", "General English", "Speaking Club"]
        directions: dict[str, TypeCourse] = {}
        for title in titles:
            directions[title], _ = TypeCourse.objects.get_or_create(title=title)
        return directions

    def _create_courses(self, directions: dict[str, TypeCourse]) -> list[Courses]:
        CoursesProgram.objects.all().delete()
        CoursesModel.objects.all().delete()
        Courses.objects.all().delete()

        courses_data = [
            {
                "title": "IELTS Intensive 6.5+",
                "direction": directions["IELTS"],
                "photo": "img/twoWomen.png",
                "price": Decimal("18000.00"),
                "duration_months": 3,
                "discounted_price": 15000,
                "monthly_price": 5000,
                "color_theme": "dark-blue",
                "title_model": "<h3>Для тех, кто хочет результат 6.5 и выше</h3>",
                "description_model": "<p>Интенсивная подготовка с пробными тестами, разбором writing и speaking.</p>",
                "programs": ["Диагностика уровня", "Writing Task 1 и Task 2", "Speaking mock interview", "Еженедельный пробный тест"],
                "modal_image": "img/aboutUs/DUOLINGO.png",
            },
            {
                "title": "SAT Math & Verbal",
                "direction": directions["SAT"],
                "photo": "img/fon.png",
                "price": Decimal("22000.00"),
                "duration_months": 4,
                "discounted_price": 19000,
                "monthly_price": 4750,
                "color_theme": "green",
                "title_model": "<h3>Подготовка к SAT для поступления на грант</h3>",
                "description_model": "<p>Фокус на math strategies, reading reasoning и работе в тайминге экзамена.</p>",
                "programs": ["SAT Math drills", "Critical Reading", "Vocabulary in context", "Full-length practice tests"],
                "modal_image": "img/aboutUs/SAT.png",
            },
            {
                "title": "General English Upper-Intermediate",
                "direction": directions["General English"],
                "photo": "img/people.png",
                "price": Decimal("12000.00"),
                "duration_months": 5,
                "discounted_price": 9900,
                "monthly_price": 1980,
                "color_theme": "light-orange",
                "title_model": "<h3>Системный рост английского для учебы и работы</h3>",
                "description_model": "<p>Развитие разговорной речи, грамматики и словаря без отрыва от практики.</p>",
                "programs": ["Grammar in use", "Speaking every lesson", "Academic vocabulary", "Listening with analysis"],
                "modal_image": "img/aboutUs/VEC3.png",
            },
            {
                "title": "Speaking Club Weekend",
                "direction": directions["Speaking Club"],
                "photo": "img/table.png",
                "price": Decimal("6000.00"),
                "duration_months": 2,
                "discounted_price": 4500,
                "monthly_price": 2250,
                "color_theme": "warm-red",
                "title_model": "<h3>Разговорная практика без языкового барьера</h3>",
                "description_model": "<p>Живые дискуссии, актуальные темы и постоянная практика speaking в мини-группах.</p>",
                "programs": ["Topic-based discussions", "Pronunciation practice", "Debates and role play", "Feedback after each session"],
                "modal_image": "img/aboutUs/VEC2.png",
            },
        ]

        created_courses: list[Courses] = []
        for course_data in courses_data:
            programs = course_data.pop("programs")
            modal_image = course_data.pop("modal_image")

            course = Courses(**course_data)
            course.photo.save(f"{course.title}.png", self._asset(course_data["photo"]), save=False)
            course.save()

            for program_title in programs:
                CoursesProgram.objects.create(course=course, title=program_title)

            modal = CoursesModel(
                courses=course,
                title_model=course.title_model,
                description_model=course.description_model,
            )
            modal.image.save(Path(modal_image).name, self._asset(modal_image), save=False)
            modal.save()
            created_courses.append(course)

        return created_courses

    def _create_course_page(self) -> None:
        CoursesPage.objects.update_or_create(
            pk=1,
            defaults={
                "title": "Наши программы",
                "description": (
                    "<p>Выберите курс под свою цель: поднять английский, подготовиться к международному "
                    "экзамену или усилить профиль для поступления в университет.</p>"
                ),
            },
        )

    def _create_teachers(self) -> None:
        Achievement.objects.all().delete()
        Teacher.objects.all().delete()

        teachers = [
            {
                "name": "Айжан Сагынбаева",
                "photo": "img/people.png",
                "bio_title": "Кто преподает?",
                "experience": "7 лет подготовки к IELTS и академическому английскому",
                "achievements": [
                    "Подготовила более 150 студентов к IELTS",
                    "Средний рост студентов: +1.5 балла за курс",
                    "Выпускница программы academic writing trainer",
                ],
            },
            {
                "name": "Даниэль Мусаев",
                "photo": "img/twoWomen.png",
                "bio_title": "Кто преподает?",
                "experience": "5 лет подготовки к SAT и поступлению в зарубежные вузы",
                "achievements": [
                    "Консультировал абитуриентов по поступлению в США",
                    "Ведет интенсивы по SAT Math и Verbal",
                    "Работает с грантовыми кейсами старшеклассников",
                ],
            },
            {
                "name": "Мээрим Абдуллаева",
                "photo": "img/fon.png",
                "bio_title": "Кто преподает?",
                "experience": "6 лет преподавания General English и speaking practice",
                "achievements": [
                    "Специализируется на разговорном английском",
                    "Собирает индивидуальные speaking-планы для студентов",
                    "Проводит клубные занятия и дебаты на английском",
                ],
            },
        ]

        for teacher_data in teachers:
            achievements = teacher_data.pop("achievements")
            teacher = Teacher(**teacher_data)
            teacher.photo.save(f"{teacher.name}.png", self._asset(teacher_data["photo"]), save=False)
            teacher.save()
            for achievement_text in achievements:
                Achievement.objects.create(teacher=teacher, text=achievement_text)

    def _create_students_page(self) -> None:
        Students.objects.update_or_create(
            pk=1,
            defaults={
                "title": "Истории наших студентов",
                "description": "Результаты учеников, которые улучшили английский, сдали экзамены и поступили в желаемые университеты.",
                "title2": "Результат измеряется поступлением и уверенностью",
                "description2": "Мы показываем не обещания, а реальные кейсы: рост баллов, сильные эссе и успешные поступления.",
            },
        )

    def _create_student_stories(self) -> None:
        AboutStudents.objects.all().delete()
        stories = [
            (
                "Алина Токтосунова",
                "После курса IELTS Intensive Алина подняла результат с 5.0 до 6.5 и подала документы в университет Малайзии.",
                "img/aboutUs/BECB2VONTAGE.png",
                2024,
            ),
            (
                "Нурсултан Ибраимов",
                "Прошел SAT Math & Verbal, усилил профиль и получил частичный грант на обучение в Турции.",
                "img/aboutUs/DUOLINGO.png",
                2025,
            ),
            (
                "Сезим Жээнбаева",
                "На программе General English вышла на уверенный Upper-Intermediate и успешно прошла интервью на английском.",
                "img/aboutUs/IELTS.png",
                2023,
            ),
        ]
        for title, description, image_path, release_year in stories:
            obj = AboutStudents(title=title, description=description, release_year=release_year)
            obj.image.save(Path(image_path).name, self._asset(image_path), save=False)
            obj.save()

    def _create_applications(self, courses: list[Courses]) -> None:
        CourseApplication.objects.all().delete()
        applications = [
            {
                "full_name": "Айпери Осмонова",
                "grade": "11 класс",
                "student_phone": "+996 555 111 222",
                "parent_phone": "+996 700 111 222",
                "reason": "Хочу поступить в зарубежный вуз и уверенно сдать IELTS.",
                "plans": "Подать документы в университеты Южной Кореи.",
                "study_time": "2 часа в день",
                "skills": "Writing, speaking, academic vocabulary",
                "ready": "Да",
                "phone": "+996 555 111 222",
                "email": "aiperi@example.com",
                "course": courses[0],
            },
            {
                "full_name": "Эрмек Нурбаев",
                "grade": "1 курс университета",
                "student_phone": "+996 777 333 444",
                "parent_phone": "",
                "reason": "Нужен сильный английский для учебы и стажировок.",
                "plans": "Поехать по обмену через 1 год.",
                "study_time": "1.5 часа в день",
                "skills": "Разговорный английский и чтение академических текстов",
                "ready": "Да",
                "phone": "+996 777 333 444",
                "email": "ermek@example.com",
                "course": courses[2],
            },
            {
                "full_name": "Бегайым Садыкова",
                "grade": "10 класс",
                "student_phone": "+996 509 222 111",
                "parent_phone": "+996 705 222 111",
                "reason": "Хочу подготовиться к SAT и получить грант.",
                "plans": "Поступление в США после школы.",
                "study_time": "3 часа в день",
                "skills": "Math reasoning, reading speed, essay planning",
                "ready": "Да",
                "phone": "+996 509 222 111",
                "email": "begaiym@example.com",
                "course": courses[1],
            },
        ]
        for application in applications:
            CourseApplication.objects.create(**application)

    def _create_feedback(self) -> None:
        Feedback.objects.all().delete()
        for feedback in [
            {"name": "Нурзат", "phone": "+996 700 444 555", "email": "nurzat@example.com"},
            {"name": "Каныкей", "phone": "+996 555 666 777", "email": "kanykei@example.com"},
            {"name": "Тимур", "phone": "+996 777 888 999", "email": "timur@example.com"},
        ]:
            Feedback.objects.create(**feedback)

    def _reset(self) -> None:
        Achievement.objects.all().delete()
        Teacher.objects.all().delete()
        Address.objects.all().delete()
        Contacts.objects.all().delete()
        AboutObjects.objects.all().delete()
        AboutObjects2.objects.all().delete()
        AboutPage.objects.all().delete()
        CoursesProgram.objects.all().delete()
        CoursesModel.objects.all().delete()
        CourseApplication.objects.all().delete()
        Courses.objects.all().delete()
        TypeCourse.objects.all().delete()
        CoursesPage.objects.all().delete()
        Students.objects.all().delete()
        AboutStudents.objects.all().delete()
        Feedback.objects.all().delete()
        Settings.objects.all().delete()
