from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models import Sum

from .enum import STATUS_CURSUES, USER_ROLE


def validate_mentor_contract_pdf(file):
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("Файл контракта не должен превышать 5 МБ.")


class ArchiveQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_archived=False)

    def archived(self):
        return self.filter(is_archived=True)


class ArchiveBase(models.Model):
    is_archived = models.BooleanField(default=False, verbose_name="В архиве")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивации")

    objects = ArchiveQuerySet.as_manager()

    class Meta:
        abstract = True


class User(AbstractUser):
    phone_number = models.CharField(
        max_length=155,
        verbose_name='номер телефона' 
    )
    role = models.CharField(
        max_length=32,
        choices=USER_ROLE,
        default="Администратор",
        verbose_name="Роль",
    )
    
    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Пользователи'
        verbose_name_plural = 'Пользователи'


class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название организации")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Слаг")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"


class Mentor(models.Model):
    class PaymentForm(models.TextChoices):
        FIXED = "fixed", "Фиксированная"
        PER_LESSON = "per_lesson", "За занятие"
        HOURLY = "hourly", "Почасовая"
        PERCENTAGE = "percentage", "Процент с ученика"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="mentors",
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="mentor_profile",
        verbose_name="Пользователь",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    is_archived = models.BooleanField(default=False, verbose_name="В архиве")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивации")

    middle_name = models.CharField("Отчество", max_length=150, blank=True, default="")
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    skills = models.CharField("Навыки", max_length=255, blank=True, default="")
    workplace = models.CharField("Место работы", max_length=255, blank=True, default="")
    documents_folder = models.CharField(
        "Папка с документами",
        max_length=500,
        blank=True,
        default="",
        help_text="Ссылка или путь к папке",
    )

    payment_form = models.CharField(
        "Форма оплаты",
        max_length=16,
        choices=PaymentForm.choices,
        default=PaymentForm.FIXED,
    )
    payment_rate = models.DecimalField(
        "Ставка оплаты",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Для почасовой или за занятие",
    )
    fixed_rate = models.DecimalField(
        "Фикс. ставка",
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    percentage_rate = models.DecimalField(
        "Процент с ученика (%)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Например, 30 для 30%%",
    )

    contract_file = models.FileField(
        "Контракт (PDF)",
        upload_to="mentor_contracts/%Y/%m/",
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf"]),
            validate_mentor_contract_pdf,
        ],
    )
    note = models.TextField("Примечание", blank=True, default="")

    departure_date = models.DateField("Дата ухода", null=True, blank=True)
    departure_reason = models.CharField("Причина ухода", max_length=255, blank=True, default="")

    def __str__(self):
        return f"{self.user.username}"

    class Meta:
        verbose_name = "Ментор"
        verbose_name_plural = "Менторы"


class Student(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активный"
        INACTIVE = "inactive", "Неактивный"
        LEFT = "left", "Ушел"
        FROZEN = "frozen", "Замороженный"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="students",
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Статус",
    )
    middle_name = models.CharField("Отчество", max_length=150, blank=True, default="")
    gender = models.CharField("Пол", max_length=10, blank=True, default="", choices=[("", "—"), ("М", "Мужской"), ("Ж", "Женский")])
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    telegram_nick = models.CharField("Ник в Telegram", max_length=100, blank=True, default="")
    from_where = models.CharField("Откуда", max_length=255, blank=True, default="")
    documents_folder = models.CharField("Папка с документами", max_length=255, blank=True, default="")
    parent_phone = models.CharField("Номер родителя", max_length=20, blank=True, default="")
    note = models.TextField("Примечание", blank=True, default="")
    is_archived = models.BooleanField(default=False, verbose_name="В архиве")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивации")
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления: '
    )

    def __str__(self):
        return f"{self.user.username}"

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"


class Parent(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="parents",
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="parent_profile",
        verbose_name="Пользователь",
    )
    students = models.ManyToManyField(
        Student,
        blank=True,
        verbose_name="Студенты",
        related_name="parents",
    )
    phone_number = models.CharField("Телефон", max_length=20, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    is_archived = models.BooleanField(default=False, verbose_name="В архиве")

    def __str__(self):
        return f"{self.user.username}"

    class Meta:
        verbose_name = "Родитель"
        verbose_name_plural = "Родители"


class Cursues(ArchiveBase):
    class CourseType(models.TextChoices):
        GROUP = "group", "Групповые"
        INDIVIDUAL = "individual", "Индивидуальные"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="courses",
    )
    title = models.CharField(max_length=155, verbose_name="Название курса")
    course_type = models.CharField(
        max_length=16,
        choices=CourseType.choices,
        default=CourseType.GROUP,
        verbose_name="Тип курса",
    )
    start = models.DateField(verbose_name="Начало курса")
    end = models.DateField(verbose_name="Конец курса", null=True, blank=True)
    lessons_per_month = models.PositiveIntegerField(default=15, verbose_name="Уроков в месяц")
    duration_days = models.PositiveIntegerField(default=0, verbose_name="Длительность (дней)")
    status = models.CharField(choices=STATUS_CURSUES, max_length=155, verbose_name="Статус")
    subject = models.CharField(max_length=155, blank=True, verbose_name="Предмет")
    price = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Цена (с.)"
    )
    capacity = models.PositiveIntegerField(default=10, verbose_name="Лимит студентов")
    room = models.CharField(max_length=64, blank=True, verbose_name="Кабинет")
    schedule_note = models.CharField(max_length=255, blank=True, verbose_name="Расписание")
    mentors = models.ManyToManyField(Mentor, blank=True, verbose_name="Менторы")
    students = models.ManyToManyField(Student, blank=True, verbose_name="Студенты")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.title
    
    @property
    def duration_label(self) -> str:
        days = int(self.duration_days or 0)
        if days <= 0:
            return "—"
        months = max(1, round(days / 30))
        if months % 10 == 1 and months % 100 != 11:
            word = "месяц"
        elif months % 10 in (2, 3, 4) and months % 100 not in (12, 13, 14):
            word = "месяца"
        else:
            word = "месяцев"
        return f"{months} {word}"

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"


class GroupCourse(Cursues):
    class Meta:
        proxy = True
        verbose_name = "Групповой курс"
        verbose_name_plural = "Групповые"


class IndividualCourse(Cursues):
    class Meta:
        proxy = True
        verbose_name = "Индивидуальный курс"
        verbose_name_plural = "Индивидуальные"


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    course = models.ForeignKey(Cursues, on_delete=models.CASCADE, verbose_name="Курс")
    tuition_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Сумма к оплате (с.)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return f"{self.student} — {self.course}"

    @property
    def paid_total(self):
        return (
            Payment.objects.filter(student=self.student, course=self.course).aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )

    @property
    def debt(self):
        return self.tuition_amount - self.paid_total

    class Meta:
        verbose_name = "Оплата за учебу"
        verbose_name_plural = "Оплата за учебу"
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="uniq_student_course")
        ]


class CourseDrop(models.Model):
    course = models.ForeignKey(Cursues, on_delete=models.CASCADE, verbose_name="Курс")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    dropped_at = models.DateField(auto_now_add=True, verbose_name="Дата")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Причина")

    def __str__(self):
        return f"{self.student} — {self.course}"

    class Meta:
        verbose_name = "Покинули курс"
        verbose_name_plural = "Покинули курс"


class CourseContract(models.Model):
    course = models.ForeignKey(Cursues, on_delete=models.CASCADE, verbose_name="Курс")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    periods = models.CharField(max_length=255, verbose_name="Периоды")
    amount_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Сумма на момент создания",
    )
    paid_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Оплачено на момент создания",
    )
    debt_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Долг на момент создания",
    )
    document_text = models.TextField(blank=True, verbose_name="Текст контракта")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Контракт {self.course} — {self.student}"

    class Meta:
        verbose_name = "Контракт курса"
        verbose_name_plural = "Контракты курсов"
        constraints = [
            models.UniqueConstraint(fields=["course", "student"], name="uniq_course_contract"),
        ]


class DebtorEnrollment(Enrollment):
    class Meta:
        proxy = True
        verbose_name = "Должник"
        verbose_name_plural = "Должники"


class StudentPayments(Enrollment):
    class Meta:
        proxy = True
        verbose_name = "Оплата за учебу"
        verbose_name_plural = "Оплата за учебу"


class Lead(ArchiveBase):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        IN_PROGRESS = "in_progress", "В работе"
        WON = "won", "Успешно"
        LOST = "lost", "Потерян"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="leads",
    )
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    phone_number = models.CharField(max_length=64, verbose_name="Телефон")
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.NEW, verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Лид"
        verbose_name_plural = "Лиды"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Наличные"
        BANK = "bank", "Банковский перевод"
        CARD = "card", "Карта"
        AITI_TRANSFER = "aiti_transfer", "Aiti переводы"
        AITI_CASH = "aiti_cash", "Aiti наличка"
        OTHER = "other", "Другое"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="payments",
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    course = models.ForeignKey(
        Cursues, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Курс"
    )
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.CASH,
        verbose_name="Способ оплаты",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_voided = models.BooleanField(default=False, verbose_name="Аннулирован")
    receipt_file = models.FileField(upload_to="receipts/", blank=True, null=True, verbose_name="Квитанция")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    def __str__(self):
        return f"{self.student} — {self.amount}"

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"


class TuitionPayment(Payment):
    class Meta:
        proxy = True
        verbose_name = "Оплата за учебу"
        verbose_name_plural = "Оплата за учебу"


class Salary(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="salaries",
    )
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, verbose_name="Ментор", related_name="salaries")
    course = models.ForeignKey(
        Cursues,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Курс",
        related_name="salaries",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма")
    comment = models.TextField("Комментарий", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    def __str__(self):
        return f"{self.mentor} — {self.amount}"

    class Meta:
        verbose_name = "Зарплата"
        verbose_name_plural = "Зарплаты"


class Task(ArchiveBase):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="tasks",
    )
    title = models.CharField(max_length=255, verbose_name="Задача")
    due_date = models.DateField(null=True, blank=True, verbose_name="Срок")
    is_done = models.BooleanField(default=False, verbose_name="Выполнено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
    

class CalendarEvent(ArchiveBase):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="calendar_events",
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    course = models.ForeignKey(
        "Cursues",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Курс",
    )
    start_at = models.DateTimeField(verbose_name="Начало")
    end_at = models.DateTimeField(null=True, blank=True, verbose_name="Конец")
    location = models.CharField(max_length=255, blank=True, verbose_name="Место проведения")
    online_link = models.URLField(blank=True, verbose_name="Ссылка на онлайн-конференцию")
    description = models.TextField(blank=True, verbose_name="Описание")
    note = models.TextField(blank=True, verbose_name="Заметка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "Календарь"


class Call(ArchiveBase):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        DONE = "done", "Завершен"
        MISSED = "missed", "Пропущен"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="calls",
    )
    contact_name = models.CharField(max_length=255, verbose_name="Контакт")
    phone_number = models.CharField(max_length=64, verbose_name="Телефон")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW, verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return f"{self.contact_name} ({self.phone_number})"

    class Meta:
        verbose_name = "Звонок"
        verbose_name_plural = "Звонки"


class AccountingEntry(ArchiveBase):
    class Type(models.TextChoices):
        INCOME = "income", "Приход"
        EXPENSE = "expense", "Расход"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="accounting_entries",
    )
    entry_type = models.CharField(max_length=16, choices=Type.choices, verbose_name="Тип")
    title = models.CharField(max_length=255, verbose_name="Описание")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    operated_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата операции")
    account = models.ForeignKey(
        "AccountingAccount",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entries",
        verbose_name="Счет",
    )
    project = models.ForeignKey(
        "AccountingProject",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entries",
        verbose_name="Проект",
    )
    category = models.ForeignKey(
        "AccountingCategory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entries",
        verbose_name="Категория",
    )
    transfer_group = models.CharField(max_length=64, blank=True, default="", verbose_name="Группа перевода")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Проводка"
        verbose_name_plural = "Бухгалтерия"


class AccountingAccount(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="accounts",
    )
    title = models.CharField(max_length=120, verbose_name="Название")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Счет"
        verbose_name_plural = "Счета"


class AccountingProject(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="projects",
    )
    title = models.CharField(max_length=120, verbose_name="Название")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"


class AccountingCategory(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="categories",
    )
    title = models.CharField(max_length=120, verbose_name="Название")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class AppSetting(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="settings",
    )
    key = models.CharField(max_length=128, unique=True, verbose_name="Ключ")
    value = models.CharField(max_length=255, blank=True, verbose_name="Значение")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = "Настройка"
        verbose_name_plural = "Настройки"


class BillingRecord(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активно"
        EXPIRED = "expired", "Истекло"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="billing_records",
    )
    name = models.CharField(max_length=255, verbose_name="Название")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, verbose_name="Статус")
    expires_at = models.DateField(null=True, blank=True, verbose_name="Дата окончания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Биллинг"
        verbose_name_plural = "Биллинг"


class AboutPage(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="about_pages",
    )
    title = models.CharField(max_length=255, default="О нас", verbose_name="Заголовок")
    body = models.TextField(blank=True, verbose_name="Текст")
    feedback_phone = models.CharField(max_length=64, blank=True, verbose_name="Телефон для отзыва")
    feedback_whatsapp = models.CharField(max_length=64, blank=True, verbose_name="WhatsApp для отзыва")
    feedback_email = models.EmailField(blank=True, verbose_name="Email для отзыва")
    feedback_person = models.CharField(max_length=255, blank=True, verbose_name="Контактное лицо (подпись)")

    about_subtitle = models.CharField(max_length=255, blank=True, verbose_name="Подзаголовок (О нас)")
    about_text = models.TextField(blank=True, verbose_name="Текст (О нас)")
    about_site_url = models.URLField(blank=True, verbose_name="Ссылка на сайт")

    contacts_text = models.TextField(blank=True, verbose_name="Текст (Контакты)")
    contacts_phone = models.CharField(max_length=64, blank=True, verbose_name="Телефон (Контакты)")
    contacts_whatsapp = models.CharField(max_length=64, blank=True, verbose_name="WhatsApp (Контакты)")
    contacts_email = models.EmailField(blank=True, verbose_name="Email (Контакты)")

    privacy_text = models.TextField(blank=True, verbose_name="Политика конфиденциальности (текст)")
    agreement_text = models.TextField(blank=True, verbose_name="Пользовательское соглашение (текст)")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "О нас"
        verbose_name_plural = "О нас"
