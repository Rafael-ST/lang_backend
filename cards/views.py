from rest_framework import filters, viewsets

from cards.filters import CardFilterBackend
from cards.models import Card
from cards.serializers import CardSerializer
from rest_framework.permissions import IsAuthenticated


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
