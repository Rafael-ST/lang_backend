from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from perfil.models import DEFAULT_PROFILE_POINTS, Perfil


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(
            user=instance,
            defaults={'pontos': DEFAULT_PROFILE_POINTS},
        )


@receiver(post_delete, sender=Perfil)
def delete_perfil_picture(sender, instance, **kwargs):
    if instance.profile_picture:
        instance.profile_picture.delete(save=False)
