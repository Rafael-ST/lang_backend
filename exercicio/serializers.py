from rest_framework import serializers

from cards.models import Card
from cards.serializers import CardSerializer
from ExerciseSet.serializers import ExerciseSetSerializer
from exercicio.models import Exercise, ExerciseAttempt


class ExerciseSerializer(serializers.ModelSerializer):
    card_detail = CardSerializer(source='card', read_only=True)
    pair_card_details = CardSerializer(source='pair_cards', many=True, read_only=True)
    exercise_set_detail = ExerciseSetSerializer(source='exercise_set', read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'id',
            'exercise_set',
            'exercise_set_detail',
            'card',
            'card_detail',
            'pair_cards',
            'pair_card_details',
            'type',
            'skill',
            'prompt',
            'options',
            'answer_config',
            'is_active',
            'difficulty',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        exercise_type = attrs.get('type', getattr(self.instance, 'type', None))
        pair_cards = attrs.get('pair_cards')

        if (
            'skill' not in attrs and
            (self.instance is None or 'type' in attrs)
        ):
            attrs['skill'] = Exercise.default_skill_for_type(exercise_type)

        if exercise_type == Exercise.ExerciseType.MATCHING_PAIRS:
            if pair_cards is None and self.instance:
                pair_cards = self.instance.pair_cards.all()

            if not pair_cards or len(pair_cards) < 2:
                raise serializers.ValidationError({
                    'pair_cards': 'Selecione pelo menos dois cards para a associacao.'
                })

            pair_card_ids = [card.pk for card in pair_cards]
            if len(pair_card_ids) != len(set(pair_card_ids)):
                raise serializers.ValidationError({
                    'pair_cards': 'Nao selecione o mesmo card mais de uma vez.'
                })

            invalid_cards = [
                card for card in pair_cards
                if not card.is_active
                or not card.english_name.strip()
                or not card.international_name.strip()
            ]
            if invalid_cards:
                raise serializers.ValidationError({
                    'pair_cards': (
                        'Todos os cards devem estar ativos e possuir nomes '
                        'em ingles e traduzido.'
                    )
                })

        if exercise_type == Exercise.ExerciseType.COMPLETE_AUDIO_TEXT:
            prompt = attrs.get('prompt', getattr(self.instance, 'prompt', {}))
            answer_config = attrs.get(
                'answer_config',
                getattr(self.instance, 'answer_config', {}),
            )
            card = attrs.get('card', getattr(self.instance, 'card', None))
            template = prompt.get('text', '') if isinstance(prompt, dict) else ''
            correct_text = (
                answer_config.get('correct_text', '')
                if isinstance(answer_config, dict)
                else ''
            )
            audio_url = (
                prompt.get('audio_url')
                if isinstance(prompt, dict)
                else None
            )

            if template.count('__') != 1:
                raise serializers.ValidationError({
                    'prompt': (
                        'O texto deve conter exatamente uma lacuna representada por __.'
                    )
                })
            if not str(correct_text).strip():
                raise serializers.ValidationError({
                    'answer_config': 'Informe o texto correto da lacuna.'
                })
            if not audio_url and not getattr(card, 'audio', None):
                raise serializers.ValidationError({
                    'card': 'O card selecionado deve possuir audio.'
                })

        if exercise_type == Exercise.ExerciseType.IMAGE_PRESENTATION:
            card = attrs.get('card', getattr(self.instance, 'card', None))
            if not getattr(card, 'image', None):
                raise serializers.ValidationError({
                    'card': 'O card selecionado deve possuir uma imagem.'
                })
            if not getattr(card, 'audio', None):
                raise serializers.ValidationError({
                    'card': 'O card selecionado deve possuir audio.'
                })
            if not str(getattr(card, 'international_name', '')).strip():
                raise serializers.ValidationError({
                    'card': 'O card selecionado deve possuir traducao.'
                })

        if exercise_type == Exercise.ExerciseType.IMAGE_MULTIPLE_CHOICE_ENGLISH:
            card = attrs.get('card', getattr(self.instance, 'card', None))
            options = attrs.get('options', getattr(self.instance, 'options', []))
            option_ids = [
                str(option.get('id'))
                for option in options
                if isinstance(option, dict) and option.get('id')
            ]

            if not getattr(card, 'image', None):
                raise serializers.ValidationError({
                    'card': 'O card correto deve possuir uma imagem.'
                })
            if len(option_ids) != 4 or len(set(option_ids)) != 4:
                raise serializers.ValidationError({
                    'options': 'Selecione exatamente quatro cards diferentes.'
                })
            if str(card.pk) not in option_ids:
                raise serializers.ValidationError({
                    'options': 'As alternativas devem incluir o card correto.'
                })

            option_cards = Card.objects.filter(id__in=option_ids)
            if option_cards.count() != 4:
                raise serializers.ValidationError({
                    'options': 'Uma ou mais alternativas nao existem.'
                })
            invalid_options = [
                option_card
                for option_card in option_cards
                if not option_card.is_active
                or not option_card.english_name.strip()
                or not option_card.audio
            ]
            if invalid_options:
                raise serializers.ValidationError({
                    'options': (
                        'Todas as alternativas devem estar ativas e possuir '
                        'nome em ingles e audio.'
                    )
                })

        if exercise_type == Exercise.ExerciseType.AUDIO_MULTIPLE_CHOICE_IMAGES:
            card = attrs.get('card', getattr(self.instance, 'card', None))
            options = attrs.get('options', getattr(self.instance, 'options', []))
            option_ids = [
                str(option.get('id'))
                for option in options
                if isinstance(option, dict) and option.get('id')
            ]

            if not getattr(card, 'audio', None):
                raise serializers.ValidationError({
                    'card': 'O card correto deve possuir audio.'
                })
            if not str(getattr(card, 'english_name', '')).strip():
                raise serializers.ValidationError({
                    'card': 'O card correto deve possuir nome em ingles.'
                })
            if len(option_ids) != 4 or len(set(option_ids)) != 4:
                raise serializers.ValidationError({
                    'options': 'Selecione exatamente quatro cards diferentes.'
                })
            if str(card.pk) not in option_ids:
                raise serializers.ValidationError({
                    'options': 'As alternativas devem incluir o card correto.'
                })

            option_cards = Card.objects.filter(id__in=option_ids)
            if option_cards.count() != 4:
                raise serializers.ValidationError({
                    'options': 'Uma ou mais alternativas nao existem.'
                })
            if any(
                not option_card.is_active or not option_card.image
                for option_card in option_cards
            ):
                raise serializers.ValidationError({
                    'options': (
                        'Todas as alternativas devem estar ativas e possuir imagem.'
                    )
                })

        if exercise_type == Exercise.ExerciseType.SPEAK_ENGLISH_FROM_TRANSLATION:
            prompt = attrs.get('prompt', getattr(self.instance, 'prompt', {}))
            answer_config = attrs.get(
                'answer_config',
                getattr(self.instance, 'answer_config', {}),
            )
            portuguese_text = (
                prompt.get('text', '') if isinstance(prompt, dict) else ''
            )
            expected_transcript = (
                answer_config.get('expected_transcript', '')
                if isinstance(answer_config, dict)
                else ''
            )

            if not str(portuguese_text).strip():
                raise serializers.ValidationError({
                    'prompt': 'Informe o texto que sera exibido em portugues.'
                })
            if not str(expected_transcript).strip():
                raise serializers.ValidationError({
                    'answer_config': 'Informe o texto esperado em ingles.'
                })

        return attrs


class ExerciseAttemptSerializer(serializers.ModelSerializer):
    exercise_detail = ExerciseSerializer(source='exercise', read_only=True)
    exercise_set_detail = ExerciseSetSerializer(source='exercise_set', read_only=True)
    user_detail = serializers.StringRelatedField(source='user', read_only=True)

    class Meta:
        model = ExerciseAttempt
        fields = [
            'id',
            'user',
            'user_detail',
            'exercise_set',
            'exercise_set_detail',
            'exercise',
            'exercise_detail',
            'is_correct',
            'answer',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
