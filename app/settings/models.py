from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models import Sum
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

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
    title = models.CharField(max_length=155, blank=True, default="", verbose_name="Название курса")
    course_type = models.CharField(
        max_length=16,
        choices=CourseType.choices,
        default=CourseType.GROUP,
        blank=True,
        verbose_name="Тип курса",
    )
    start = models.DateField(null=True, blank=True, verbose_name="Начало курса")
    end = models.DateField(verbose_name="Конец курса", null=True, blank=True)
    lessons_per_month = models.PositiveIntegerField(null=True, blank=True, default=15, verbose_name="Уроков в месяц")
    duration_days = models.PositiveIntegerField(null=True, blank=True, default=0, verbose_name="Длительность (дней)")
    status = models.CharField(choices=STATUS_CURSUES, max_length=155, blank=True, default="", verbose_name="Статус")
    subject = models.CharField(max_length=155, blank=True, default="", verbose_name="Предмет")
    price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, default=0, verbose_name="Цена (с.)"
    )
    capacity = models.PositiveIntegerField(null=True, blank=True, default=10, verbose_name="Лимит студентов")
    room = models.CharField(max_length=64, blank=True, default="", verbose_name="Кабинет")
    schedule_note = models.CharField(max_length=255, blank=True, default="", verbose_name="Расписание")
    mentors = models.ManyToManyField(Mentor, blank=True, verbose_name="Менторы")
    students = models.ManyToManyField(Student, blank=True, verbose_name="Студенты")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.title or "Курс без названия"
    
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
        NEW = "new", "Консультация"
        IN_PROGRESS = "in_progress", "Ожидание"
        INVITED = "invited", "Приглашен(а) на открытый урок"
        PARTICIPATED = "participated", "Участвовал(а) на открытом уроке"
        WON = "won", "Уже учится"
        LOST = "lost", "Потерянный лид"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name="leads",
    )
    first_name = models.CharField("Имя", max_length=150, blank=True, default="")
    last_name = models.CharField("Фамилия", max_length=150, blank=True, default="")
    middle_name = models.CharField("Отчество", max_length=150, blank=True, default="")
    full_name = models.CharField(
        max_length=255,
        blank=True,
        default="Посетитель сайта",
        verbose_name="ФИО",
    )
    phone_number = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Телефон",
    )
    email = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Email",
    )
    extra_phone = models.CharField("Дополнительный номер", max_length=64, blank=True, default="")
    telegram_nick = models.CharField("Ник в Telegram", max_length=100, blank=True, default="")
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    due_date = models.DateField("Крайний срок", null=True, blank=True)
    from_where = models.CharField("Откуда", max_length=255, blank=True, default="")
    channel = models.CharField("Канал", max_length=64, blank=True, default="")
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ответственный",
        related_name="assigned_leads",
    )
    subject_interest = models.CharField("Интересуется предметом", max_length=255, blank=True, default="")
    interested_courses = models.TextField("Интересующие курсы", blank=True, default="")
    labels = models.CharField("Метки", max_length=255, blank=True, default="")
    comment = models.TextField("Комментарий", blank=True, default="")
    lost_reason = models.CharField("Причина потери лида", max_length=255, blank=True, default="")
    source = models.CharField(
        max_length=32,
        blank=True,
        default="manual",
        verbose_name="Источник",
    )
    session_key = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        verbose_name="Сессия чата",
    )
    message = models.TextField(
        blank=True,
        default="",
        verbose_name="Последний вопрос",
    )
    bot_reply = models.TextField(
        blank=True,
        default="",
        verbose_name="Последний ответ бота",
    )
    conversation_log = models.TextField(
        blank=True,
        default="",
        verbose_name="История переписки",
    )
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
        MBANK = "mbank", "МБанк"
        CASH = "cash", "Наличкой"
        BOOK = "book", "За Книгу"
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


class CurriculumModule(models.Model):
    """Блок учебного плана курса (например «Месяц 1 — Основы Python»). Заполняется в CRM; ментор видит только в кабинете."""

    course = models.ForeignKey(
        Cursues,
        on_delete=models.CASCADE,
        related_name="curriculum_modules",
        verbose_name="Курс",
    )
    order = models.PositiveSmallIntegerField(verbose_name="Номер модуля", default=1)
    title = models.CharField(max_length=255, verbose_name="Название модуля")

    class Meta:
        verbose_name = "Модуль учебного плана"
        verbose_name_plural = "Модули учебного плана"
        ordering = ["course_id", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order"],
                name="uniq_curriculum_module_course_order",
            )
        ]

    def __str__(self):
        return f"{self.course.title}: Месяц {self.order}. {self.title}"


class Lesson(ArchiveBase):
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        verbose_name="Ментор",
        related_name="lessons"
    )
    course = models.ForeignKey(
        Cursues,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Курс",
        related_name="lessons"
    )
    curriculum_module = models.ForeignKey(
        CurriculumModule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Модуль учебного плана",
        related_name="lessons",
    )
    title = models.CharField(max_length=255, verbose_name="Тема урока")
    description = models.TextField(blank=True, verbose_name="Описание урока")
    order = models.PositiveIntegerField(verbose_name="Порядок")
    is_additional = models.BooleanField(default=False, verbose_name="Дополнительный урок")
    date = models.DateField(null=True, blank=True, verbose_name="Дата урока")
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Дедлайн домашнего задания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"{self.title} ({self.mentor.user.username})"

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ["order"]


class Exam(ArchiveBase):
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        verbose_name="Ментор",
        related_name="exams"
    )
    title = models.CharField(max_length=255, verbose_name="Название контрольной работы")
    description = models.TextField(blank=True, verbose_name="Описание")
    deadline = models.DateTimeField(verbose_name="Дедлайн")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return f"{self.title} ({self.mentor.user.username})"

    class Meta:
        verbose_name = "Контрольная работа"
        verbose_name_plural = "Контрольные работы"
        ordering = ["-created_at"]


class LessonLink(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        verbose_name="Урок",
        related_name="links"
    )
    title = models.CharField(max_length=255, verbose_name="Название ссылки")
    url = models.URLField(verbose_name="URL ссылки")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return f"{self.title} ({self.lesson.title})"

    class Meta:
        verbose_name = "Ссылка урока"
        verbose_name_plural = "Ссылки уроков"
        ordering = ["order"]


class Homework(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        verbose_name="Урок",
        related_name="homeworks"
    )
    title = models.CharField(max_length=255, verbose_name="Название задания")
    description = models.TextField(verbose_name="Описание задания")
    file = models.FileField(
        upload_to='homeworks/',
        null=True,
        blank=True,
        verbose_name="Файл задания"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"{self.title} ({self.lesson.title})"

    class Meta:
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"
        ordering = ["-created_at"]


class StudentGrade(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        verbose_name="Урок",
        related_name="grades"
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        verbose_name="Студент",
        related_name="lesson_grades"
    )
    grade = models.IntegerField(
        choices=[(0, '0'), (1, '1')],
        verbose_name="Оценка"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Оценка студента"
        verbose_name_plural = "Оценки студентов"
        unique_together = ['lesson', 'student']


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('homework', 'Домашнее задание'),
        ('grade', 'Оценка'),
        ('message', 'Сообщение'),
        ('system', 'Системное'),
    ]
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Получатель",
        related_name="notifications"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Отправитель",
        related_name="sent_notifications"
    )
    type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system',
        verbose_name="Тип уведомления"
    )
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    message = models.TextField(verbose_name="Сообщение")
    related_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Связанный урок",
        related_name="notifications"
    )
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return f"{self.title} → {self.recipient.username}"

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]


class TimeSlot(models.Model):
    DAYS_OF_WEEK = [
        ('monday', 'Понедельник'),
        ('tuesday', 'Вторник'),
        ('wednesday', 'Среда'),
        ('thursday', 'Четверг'),
        ('friday', 'Пятница'),
        ('saturday', 'Суббота'),
        ('sunday', 'Воскресенье'),
    ]
    
    day_of_week = models.CharField(
        max_length=10,
        choices=DAYS_OF_WEEK,
        verbose_name="День недели"
    )
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time} - {self.end_time}"

    class Meta:
        verbose_name = "Временной слот"
        verbose_name_plural = "Временные слоты"
        ordering = ['day_of_week', 'start_time']


class Schedule(models.Model):
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        verbose_name="Ментор",
        related_name="schedules"
    )
    course = models.ForeignKey(
        Cursues,
        on_delete=models.CASCADE,
        verbose_name="Курс",
        related_name="schedules"
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        verbose_name="Временной слот",
        related_name="schedules"
    )
    room = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Кабинет/Комната"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"{self.mentor.user.username} - {self.course.title} - {self.time_slot}"

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписания"
        unique_together = ['mentor', 'course', 'time_slot']
        ordering = ['time_slot__day_of_week', 'time_slot__start_time']


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


def _course_students_through_kwargs(course_id, student_id):
    field = Cursues._meta.get_field("students")
    return {
        f"{field.m2m_field_name()}_id": course_id,
        f"{field.m2m_reverse_field_name()}_id": student_id,
    }


@receiver(m2m_changed, sender=Cursues.students.through)
def sync_enrollments_from_course_students(sender, instance, action, reverse, pk_set, using, **kwargs):
    if action not in {"post_add", "post_remove", "post_clear"}:
        return

    enrollment_qs = Enrollment.objects.using(using)

    if action == "post_add" and pk_set:
        if reverse:
            student = instance
            for course in Cursues.objects.using(using).filter(pk__in=pk_set):
                enrollment_qs.get_or_create(
                    student_id=student.pk,
                    course_id=course.pk,
                    defaults={"tuition_amount": course.price or 0},
                )
        else:
            course = instance
            for student_id in pk_set:
                enrollment_qs.get_or_create(
                    student_id=student_id,
                    course_id=course.pk,
                    defaults={"tuition_amount": course.price or 0},
                )
        return

    if action == "post_remove" and pk_set:
        if reverse:
            enrollment_qs.filter(student=instance, course_id__in=pk_set).delete()
        else:
            enrollment_qs.filter(course=instance, student_id__in=pk_set).delete()
        return

    if action == "post_clear":
        if reverse:
            enrollment_qs.filter(student=instance).delete()
        else:
            enrollment_qs.filter(course=instance).delete()


@receiver(post_save, sender=Enrollment)
def sync_course_students_from_enrollment(sender, instance, using, **kwargs):
    if not instance.course_id or not instance.student_id:
        return
    Cursues.students.through.objects.using(using).get_or_create(
        **_course_students_through_kwargs(instance.course_id, instance.student_id)
    )


@receiver(post_delete, sender=Enrollment)
def remove_course_student_from_deleted_enrollment(sender, instance, using, **kwargs):
    if not instance.course_id or not instance.student_id:
        return
    Cursues.students.through.objects.using(using).filter(
        **_course_students_through_kwargs(instance.course_id, instance.student_id)
    ).delete()
