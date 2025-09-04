from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Wallet

@receiver(post_save, sender=CustomUser)
def create_wallet_for_mse(sender, instance, created, **kwargs):
    if created and instance.is_mse:
        Wallet.objects.create(owner=instance)
