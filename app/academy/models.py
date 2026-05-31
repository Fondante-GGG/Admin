from django.db import models
from ckeditor.fields import RichTextField

class Settings(models.Model):
    title_banner = models.CharField(
        max_length=155,
        verbose_name='Заголовок Баннер'
    )
    description_banner = RichTextField(
        verbose_name='Описание Баннер'
    )
    title_about= models.CharField(
        max_length=155,
        verbose_name='Заголовок О нас'
    )
    image_about = models.ImageField(
        upload_to='settings',
        verbose_name='Фото'
    )
    description_about = RichTextField(
        verbose_name='Описание О нас 1'
    )
    title_about2 = models.CharField(max_length = 155, verbose_name = 'описания материала')
    description_about2 = RichTextField(
        verbose_name='Описание О нас 2'
    )
    description_about3 = RichTextField(
        verbose_name='Описание О нас 3'
    )
    description_about4 = RichTextField(
        verbose_name='Описание О нас 4'
    )
    popular_courses = models.CharField(
        max_length=155,
        verbose_name='Популярные курсы'
    )
    our_teachers = models.CharField(
        max_length=155,
        verbose_name='Наши преподы'
    )
    feedback = models.CharField(
        max_length=155,
        verbose_name='Заголоаок обратный связи'
    )
    feedback_description = RichTextField(
        verbose_name='Описание обратной связи '
    )
    linksinsta=models.URLField(verbose_name='инста')
    linksyoutube=models.URLField(verbose_name='ютуб')
    linkstiktok=models.URLField(verbose_name='тикток')

    def __str__(self):
        return self.title_banner

    class Meta:
        verbose_name_plural = 'Настрокий Главной Страницы'

class Contacts(models.Model):
    phone_numbers = RichTextField(verbose_name='номер телефона')
    email = models.CharField(verbose_name = 'почта', max_length=155)
    address = models.CharField(verbose_name = 'адрес', max_length=155)
    links_email = models.URLField(verbose_name='Ссылка на почту')
    links_address = models.URLField(verbose_name='Ссылка на адрес')

    class Meta:
        verbose_name_plural = 'Настрокий контакты'


class Address(models.Model):
    contact = models.ForeignKey(
        Contacts,
        related_name="addresses",
        on_delete=models.CASCADE
    )
    address = models.CharField(verbose_name='адрес', max_length=155)
    link = models.URLField(verbose_name='Ссылка на адрес')

    class Meta:
        verbose_name_plural = "Адреса"

    def __str__(self):
        return self.address

class Teacher(models.Model):
    name = models.CharField(max_length=255, verbose_name="ФИО преподавателя")
    photo = models.ImageField(upload_to='teachers/', verbose_name="Фото")
    bio_title = models.CharField(max_length=255, default="Кто преподает?", verbose_name="Заголовок")
    experience = models.CharField(max_length=255, verbose_name="Опыт работы")

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"

    def __str__(self):
        return self.name


class Achievement(models.Model):
    teacher = models.ForeignKey(Teacher, related_name='achievements', on_delete=models.CASCADE)
    text = models.CharField(max_length=255, verbose_name="Достижение")

    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"

    def __str__(self):
        return self.text

class AboutPage(models.Model):
    title_banner = models.CharField(
        max_length=155,
        verbose_name='Заголовка Баннера'
    )
    description_banner = RichTextField(
        verbose_name='Описание Баннера'
    )
    title = models.CharField(
        max_length=155,
        verbose_name='Заголовка О нас'
    )
    description = RichTextField(
        verbose_name='Описание о нас'
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Настройки страницы о нас"
        verbose_name_plural = "Настройки страницы о нас"

class AboutObjects(models.Model):
    title = models.CharField(
        max_length=155,
        verbose_name='Заголовка'
    )
    description = RichTextField(
        verbose_name='Описание'
    )
    image = models.ImageField(
        upload_to='about',
        verbose_name='Фото'
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Данный'
        verbose_name_plural = 'Данные'

class AboutObjects2(models.Model):
    title = models.CharField(
        max_length=155,
        verbose_name='Заголовка'
    )
    description = RichTextField(
        verbose_name='Описание'
    )
    image = models.ImageField(
        upload_to='about',
        verbose_name='Фото'
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Данный 2'
        verbose_name_plural = 'Данные 2'

class TypeCourse(models.Model):
    title = models.CharField(max_length=255, blank=True, default="", verbose_name='тип курсов')

    def __str__(self):
        return self.title or "Тип курса"


class Courses(models.Model):
    title = models.CharField(max_length=255, blank=True, default="", verbose_name='заголовок')
    direction = models.ForeignKey(TypeCourse, on_delete = models.SET_NULL, null=True, blank=True, verbose_name='направление')
    photo = models.ImageField(upload_to = 'courses/', null=True, blank=True, verbose_name = 'фото')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена")
    duration_months = models.PositiveIntegerField(null=True, blank=True, verbose_name="Продолжительность (мес.)")
    discounted_price = models.IntegerField(null=True, blank=True)
    monthly_price = models.IntegerField(null=True, blank=True)
    color_theme = models.CharField(max_length=50, blank=True, default="", help_text="Цвет темы: light-purple, dark-blue, green и т.д.")
    title_model = RichTextField(
        blank=True,
        default="",
        verbose_name='Заголовка Модельного окна'
    )
    description_model = RichTextField(
        blank=True,
        default="",
        verbose_name='Описание Модельного окна'
    )


    @property
    def discount_percent(self):
        if self.price and self.discounted_price:
            return round((float(self.price) - float(self.discounted_price)) / float(self.price) * 100)
        return 0

    def __str__(self):
        return self.title or "Курс без названия"
    
    class Meta:
        verbose_name_plural = 'Курсы'
    
class CoursesProgram(models.Model):
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, related_name='programs')
    title = models.CharField(max_length=155, blank=True, default="", verbose_name='Заголовка')

    def __str__(self):
        return self.title or "Программа курса"
    

class CoursesModel(models.Model):
    courses = models.ForeignKey(Courses, on_delete= models.SET_NULL, null=True, blank=True, related_name='modals')
    title_model = RichTextField(
        blank=True,
        default="",
        verbose_name='Заголовка Модельного окна'
    )
    description_model = RichTextField(
        blank=True,
        default="",
        verbose_name='Описание Модельного окна'
    )
    image = models.ImageField(
        upload_to='courses',
        null=True,
        blank=True,
        verbose_name='Фото'
    )
    def __str__(self):
        return self.title_model or "Модельное окно курса"
    
    class Meta:
        verbose_name_plural = 'модельное окно'

class CourseApplication(models.Model):
    full_name = models.CharField("Фамилия, Имя", max_length=255)
    grade = models.CharField("Класс/Университет", max_length=50, blank=True, null=True)
    student_phone = models.CharField("Телефон ученика", max_length=50, blank=True, null=True)
    parent_phone = models.CharField("Телефон родителя (WhatsApp)", max_length=50, blank=True, null=True)

    reason = models.TextField("Почему хочешь изучать английский?", blank=True, null=True)
    plans = models.TextField("Какие планы после окончания курса?", blank=True, null=True)
    study_time = models.CharField("Сколько времени готов уделять?", max_length=50, blank=True, null=True)
    skills = models.TextField("Что хочешь уметь на английском?", blank=True, null=True)
    ready = models.CharField("Готов ли посещать занятия?", max_length=10, blank=True, null=True)

    phone = models.CharField("Телефон (для связи)", max_length=50)
    email = models.EmailField("Email", blank=True, null=True)
    course = models.ForeignKey("Courses", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Заявки на курсы"

    def __str__(self):
        return f"{self.full_name} - {self.course.title}"

    


class Feedback(models.Model):
    name = models.CharField(max_length=255, verbose_name="Имя")
    phone = models.CharField(max_length=30, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"
    

class CoursesPage(models.Model):
    title = models.CharField(max_length=233, verbose_name='заголовок')
    description = RichTextField(verbose_name='описание')
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = 'настройка стр курсов'

class Students(models.Model):
    title = models.CharField(max_length=255, verbose_name='заголовок')
    description = models.TextField (verbose_name='описание')
    title2 = models.CharField(max_length=255, verbose_name='заголовок')
    description2 = models.TextField (verbose_name='описание')

class AboutStudents(models.Model):
    title = models.CharField(max_length=255, verbose_name='имя студента')
    description = models.TextField(verbose_name='описание студента')
    image = models.ImageField(
        upload_to='courses/',
        verbose_name='фото студента'
    )
    release_year = models.IntegerField(
        verbose_name='год выпуска',
        null=True,  # Можно сделать необязательным, если данные отсутствуют
        blank=True
    )

    def __str__(self):
        return self.title
        
    class Meta:
        verbose_name_plural = 'Студенты'
