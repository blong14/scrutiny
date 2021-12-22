from rest_framework.serializers import CharField, ModelSerializer

from news.models import Item


class ItemSerializer(ModelSerializer):
    class Meta:
        fields = Item.serializable_fields()
        model = Item
        optional_fields = Item.optional_fields()
