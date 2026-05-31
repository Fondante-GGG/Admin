from app.settings.models import AboutPage, AppSetting, BillingRecord


class CRMSetting(AppSetting):
    class Meta:
        proxy = True
        app_label = "app.config"
        verbose_name = "Настройки"
        verbose_name_plural = "Настройки"


class CRMBilling(BillingRecord):
    class Meta:
        proxy = True
        app_label = "app.config"
        verbose_name = "Биллинг"
        verbose_name_plural = "Биллинг"


class CRMAbout(AboutPage):
    class Meta:
        proxy = True
        app_label = "app.config"
        verbose_name = "О нас"
        verbose_name_plural = "О нас"

