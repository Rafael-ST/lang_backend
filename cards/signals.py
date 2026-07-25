from django.db.models.signals import post_delete
from django.dispatch import receiver

from cards.models import Card


@receiver(post_delete, sender=Card)
def delete_card_media(sender, instance, **kwargs):
    if instance.audio:
        instance.audio.delete(save=False)
    if instance.image:
        instance.image.delete(save=False)
