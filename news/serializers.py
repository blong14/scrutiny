from rest_framework.fields import CharField, IntegerField
from rest_framework.serializers import ModelSerializer

from news.models import Item


class ItemSerializer(ModelSerializer):
    class Meta:
        fields = Item.serializable_fields()
        model = Item

    id = IntegerField(read_only=False, required=False, allow_null=True)
    text = CharField(allow_blank=True)
