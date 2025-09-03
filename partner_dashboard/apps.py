from django.apps import AppConfig


class PartnerDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'partner_dashboard'
    verbose_name = 'Partner Dashboard'
    
    def ready(self):
        import partner_dashboard.signals
