# Generated manually for CurriculumModule and Lesson.curriculum_module

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("settings", "0031_timeslot_schedule"),
    ]

    operations = [
        migrations.CreateModel(
            name="CurriculumModule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveSmallIntegerField(default=1, verbose_name="Номер модуля")),
                ("title", models.CharField(max_length=255, verbose_name="Название модуля")),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="curriculum_modules",
                        to="settings.cursues",
                        verbose_name="Курс",
                    ),
                ),
            ],
            options={
                "verbose_name": "Модуль учебного плана",
                "verbose_name_plural": "Модули учебного плана",
                "ordering": ["course_id", "order"],
            },
        ),
        migrations.AddConstraint(
            model_name="curriculummodule",
            constraint=models.UniqueConstraint(
                fields=("course", "order"),
                name="uniq_curriculum_module_course_order",
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="curriculum_module",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="lessons",
                to="settings.curriculummodule",
                verbose_name="Модуль учебного плана",
            ),
        ),
    ]
