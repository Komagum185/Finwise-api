from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import PartnerDashboard

User = get_user_model()


@receiver(post_save, sender=User)
def create_partner_dashboard_on_user_creation(sender, instance, created, **kwargs):
    """
    Create a partner dashboard record when a new partner user is created
    """
    if created and instance.role == 'partner':
        PartnerDashboard.objects.create(
            partner=instance,
            access_count=0
        )
