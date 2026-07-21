from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from categorias.models import Categoria
from cards.models import Card
from exercicio.models import Exercise, ExerciseAttempt
from ExerciseSet.models import ExerciseSet
from niveis.models import Nivel
from niveis.serializers import NivelSerializer
from subniveis.models import SubNivel
from subniveis.progress import is_sublevel_completed_for_user
from subniveis.serializers import SubNivelSerializer


class HierarchyProgressTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='student',
            password='secret',
        )
        self.level = Nivel.objects.create(nome='A1')
        self.first_sublevel = SubNivel.objects.create(
            nome='A1.1',
            subnivel=self.level,
            ordem=1,
        )
        self.second_sublevel = SubNivel.objects.create(
            nome='A1.2',
            subnivel=self.level,
            ordem=2,
        )
        category = Categoria.objects.create(nome='Basics')
        card = Card.objects.create(
            english_name='Hello',
            international_name='Ola',
            categoria=category,
        )
        self.exercises = []

        for order, sublevel in enumerate(
            [self.first_sublevel, self.second_sublevel],
            start=1,
        ):
            exercise_set = ExerciseSet.objects.create(
                sublevel=sublevel,
                title=f'Set {order}',
                order=1,
            )
            self.exercises.append(
                Exercise.objects.create(
                    exercise_set=exercise_set,
                    card=card,
                    type=Exercise.ExerciseType.MULTIPLE_CHOICE_TRANSLATION,
                )
            )

        self.context = {'request': SimpleNamespace(user=self.user)}

    def complete_exercise(self, exercise):
        ExerciseAttempt.objects.create(
            user=self.user,
            exercise_set=exercise.exercise_set,
            exercise=exercise,
            is_correct=True,
        )

    def test_sublevel_is_completed_only_after_all_exercises(self):
        self.assertFalse(
            is_sublevel_completed_for_user(self.first_sublevel, self.user)
        )

        self.complete_exercise(self.exercises[0])

        self.assertTrue(
            is_sublevel_completed_for_user(self.first_sublevel, self.user)
        )
        self.assertTrue(
            SubNivelSerializer(
                self.first_sublevel,
                context=self.context,
            ).data['is_completed']
        )

    def test_level_is_completed_only_after_all_sublevels(self):
        self.complete_exercise(self.exercises[0])
        serializer = NivelSerializer(self.level, context=self.context)
        self.assertFalse(serializer.data['is_completed'])

        self.complete_exercise(self.exercises[1])
        serializer = NivelSerializer(self.level, context=self.context)
        self.assertTrue(serializer.data['is_completed'])
