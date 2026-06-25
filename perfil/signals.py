from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from perfil.models import Perfil


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(user=instance)
