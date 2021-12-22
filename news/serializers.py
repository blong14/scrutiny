from rest_framework.serializers import ModelSerializer

from news.models import Item


class ItemSerializer(ModelSerializer):
    class Meta:
        fields = Item.serializable_fields()
        model = Item
