from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0014_accounting_modal"),
    ]

    operations = [
        migrations.AddField(
            model_name="aboutpage",
            name="feedback_phone",
            field=models.CharField(blank=True, max_length=64, verbose_name="Телефон для отзыва"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="feedback_whatsapp",
            field=models.CharField(blank=True, max_length=64, verbose_name="WhatsApp для отзыва"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="feedback_email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="Email для отзыва"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="feedback_person",
            field=models.CharField(blank=True, max_length=255, verbose_name="Контактное лицо (подпись)"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="about_subtitle",
            field=models.CharField(blank=True, max_length=255, verbose_name="Подзаголовок (О нас)"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="about_text",
            field=models.TextField(blank=True, verbose_name="Текст (О нас)"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="about_site_url",
            field=models.URLField(blank=True, verbose_name="Ссылка на сайт"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="contacts_text",
            field=models.TextField(blank=True, verbose_name="Текст (Контакты)"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="contacts_phone",
            field=models.CharField(blank=True, max_length=64, verbose_name="Телефон (Контакты)"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="contacts_whatsapp",
            field=models.CharField(blank=True, max_length=64, verbose_name="WhatsApp (Контакты)"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="contacts_email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="Email (Контакты)"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="privacy_text",
            field=models.TextField(blank=True, verbose_name="Политика конфиденциальности (текст)"),
        ),
        migrations.AddField(
            model_name="aboutpage",
            name="agreement_text",
            field=models.TextField(blank=True, verbose_name="Пользовательское соглашение (текст)"),
        ),
    ]

