from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from exercicio.models import ExerciseAttempt
from perfil.models import DEFAULT_PROFILE_POINTS, Perfil


RECOVERY_RULES = [
    (timedelta(hours=12), 20),
    (timedelta(hours=8), 10),
]


def recover_profile_points_for_user(user):
    if not user or not user.is_authenticated:
        return None

    latest_attempt = (
        ExerciseAttempt.objects.filter(user=user)
        .order_by('-created_at')
        .only('created_at')
        .first()
    )

    if not latest_attempt:
        return None

    elapsed_time = timezone.now() - latest_attempt.created_at
    eligible_recovery = 0

    for minimum_time, points in RECOVERY_RULES:
        if elapsed_time >= minimum_time:
            eligible_recovery = points
            break

    if eligible_recovery <= 0:
        return None

    with transaction.atomic():
        profile = Perfil.objects.select_for_update().filter(user=user).first()

        if not profile:
            return None

        already_recovered = profile.pontos_recuperados_desde_ultimo_exercicio

        if (
            not profile.ultima_recuperacao_pontos_em
            or profile.ultima_recuperacao_pontos_em < latest_attempt.created_at
        ):
            already_recovered = 0

        points_to_recover = eligible_recovery - already_recovered

        if points_to_recover <= 0:
            return profile

        profile.pontos = min(DEFAULT_PROFILE_POINTS, profile.pontos + points_to_recover)
        profile.pontos_recuperados_desde_ultimo_exercicio = eligible_recovery
        profile.ultima_recuperacao_pontos_em = timezone.now()
        profile.save(
            update_fields=[
                'pontos',
                'pontos_recuperados_desde_ultimo_exercicio',
                'ultima_recuperacao_pontos_em',
                'updated_at',
            ]
        )

        return profile
