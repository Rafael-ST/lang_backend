from django.db import transaction
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from cards.filters import CardFilterBackend
from cards.models import Card, UserCardAccess
from cards.serializers import CardSerializer, MarkCardsSeenSerializer
from rest_framework.permissions import IsAdminUser, IsAuthenticated


class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all().order_by('english_name')
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        CardFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['english_name', 'international_name']
    ordering_fields = ['english_name', 'international_name', 'created_at', 'updated_at', 'is_active']
    ordering = ['english_name']

    def get_permissions(self):
        if self.action in {'create', 'update', 'partial_update', 'destroy'}:
            return [IsAdminUser()]

        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='mark-seen')
    def mark_seen(self, request):
        serializer = MarkCardsSeenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        requested_ids = list(dict.fromkeys(serializer.validated_data['card_ids']))
        cards_by_id = {
            card.id: card
            for card in Card.objects.filter(id__in=requested_ids, is_active=True)
        }
        first_seen_card_ids = []

        with transaction.atomic():
            for card_id in requested_ids:
                card = cards_by_id.get(card_id)

                if not card:
                    continue

                _, created = UserCardAccess.objects.get_or_create(
                    user=request.user,
                    card=card,
                )

                if created:
                    first_seen_card_ids.append(str(card_id))

        return Response(
            {
                'first_seen_card_ids': first_seen_card_ids,
                'seen_card_ids': [str(card_id) for card_id in cards_by_id],
            },
            status=status.HTTP_200_OK,
        )
